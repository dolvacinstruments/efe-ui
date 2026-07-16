import logging
import random
import socket
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from efe_ui.constants import CHANNEL_COUNT, VariableType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


REFRESH_INTERVAL_MS = 200


class DeviceStatusKind(StrEnum):
    OK = "OK"
    DISCONNECTED = "Disconnected"
    CONNECTION_ERROR = "Connection Error"
    IO_ERROR = "I/O Error"
    UNKNOWN_ERROR = "Unknown Error"


@dataclass
class DeviceStatus:
    kind: DeviceStatusKind
    message: str | None = None

    @classmethod
    def ok(cls) -> Self:
        return cls(kind=DeviceStatusKind.OK)


@dataclass
class DeviceSetup:
    is_enabled: list[bool]
    is_diode_mode: list[bool]
    is_high_range: list[bool]

    voltage_c: list[float]
    current_c: list[float]
    voltage_e: list[float]
    current_e: list[float]

    def __init__(self) -> None:
        self.is_disabled = [True] * CHANNEL_COUNT
        self.is_diode_mode = [True] * CHANNEL_COUNT
        self.is_high_range = [True] * CHANNEL_COUNT

        self.voltage_c = [0.0] * CHANNEL_COUNT
        self.current_c = [0.0] * CHANNEL_COUNT
        self.voltage_e = [0.0] * CHANNEL_COUNT
        self.current_e = [0.0] * CHANNEL_COUNT


@dataclass
class DeviceMeasured:
    voltage_c: list[float | None]
    voltage_e: list[float | None]
    current: list[float | None]

    def __init__(self) -> None:
        self.voltage_c = [None] * CHANNEL_COUNT
        self.voltage_e = [None] * CHANNEL_COUNT
        self.current = [None] * CHANNEL_COUNT


class EFE(QObject):
    setup_updated = Signal(DeviceSetup)
    status_updated = Signal(DeviceStatus)
    measured_updated = Signal(DeviceMeasured)

    def __init__(self, ip: str) -> None:
        super().__init__()
        self._current = DeviceSetup()
        self._new = DeviceSetup()

        self._device = RealDevice(ip)
        self._device_connected = False

    @Slot()
    def start_loop(self) -> None:

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.tick)
        self.timer.start(REFRESH_INTERVAL_MS)

    @Slot()
    def tick(self) -> None:
        if self._device_connected:
            self.update_device()
            self.poll_device()
        else:
            logger.info("Device not connected. Attempting to connect...")
            self.connect_device()
            self.query_device_setup()
        self.timer.start(REFRESH_INTERVAL_MS)

    @Slot()
    def stop_worker(self) -> None:
        self.timer.stop()
        if self._device is not None:
            self._device.close()
        self.thread().quit()

    @Slot(int, bool)
    def set_disabled(self, channel: int, is_disabled: bool) -> None:
        self._new.is_disabled[channel] = is_disabled

    @Slot(int, bool)
    def set_diode_mode(self, channel: int, is_diode_mode: bool) -> None:
        self._new.is_diode_mode[channel] = is_diode_mode

    @Slot(int, bool)
    def set_high_range(self, channel: int, is_high_range: bool) -> None:
        self._new.is_high_range[channel] = is_high_range

    @Slot(int, VariableType, float)
    def set_value(self, channel: int, variable_type: VariableType, value: float) -> None:
        if variable_type == VariableType.VOLTAGE_C:
            self._new.voltage_c[channel] = value
        elif variable_type == VariableType.CURRENT_C:
            self._new.current_c[channel] = value / 1e6
        elif variable_type == VariableType.VOLTAGE_E:
            self._new.voltage_e[channel] = value
        elif variable_type == VariableType.CURRENT_E:
            self._new.current_e[channel] = value / 1e6

    def connect_device(self) -> None:
        try:
            self._device.open()
            self._device_connected = True
            self.status_updated.emit(DeviceStatus.ok())
            return
        except DeviceConnectionError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.CONNECTION_ERROR, str(e)))
            return
        except DeviceIOError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
            return

    def poll_device(self) -> None:
        try:
            for i in range(CHANNEL_COUNT):
                if not self._current.is_disabled[i]:
                    measured = DeviceMeasured()
                    measured.voltage_c[i] = float(self._device.query(f"MEAS{i + 1}:VOLTC?"))
                    measured.current[i] = float(self._device.query(f"MEAS{i + 1}:CURR?")) * 1e6
                    if not self._current.is_diode_mode[i]:
                        measured.voltage_e[i] = float(self._device.query(f"MEAS{i + 1}:VOLTE?"))
                    self.measured_updated.emit(measured)
        except DeviceIOError as e:
            logger.error(f"Error occurred while polling device: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False

    def update_device(self) -> None:
        try:
            for i in range(CHANNEL_COUNT):
                if self._current.is_disabled[i] != self._new.is_disabled[i]:
                    if self._new.is_disabled[i]:
                        self._device.write(f"OUTP{i + 1} OFF")
                    else:
                        self._device.write(f"OUTP{i + 1} ON")
                    self._current.is_disabled[i] = self._new.is_disabled[i]

                if self._current.is_diode_mode[i] != self._new.is_diode_mode[i]:
                    if self._new.is_diode_mode[i]:
                        self._device.write(f"MODE{i + 1}:DIODE")
                    else:
                        self._device.write(f"MODE{i + 1}:NORMAL")
                    self._current.is_diode_mode[i] = self._new.is_diode_mode[i]

                if self._current.is_high_range[i] != self._new.is_high_range[i]:
                    if self._new.is_high_range[i]:
                        self._device.write(f"SOUR{i + 1}:CURR:RANG 1e-4")
                    else:
                        self._device.write(f"SOUR{i + 1}:CURR:RANG 1e-6")
                    self._current.is_high_range[i] = self._new.is_high_range[i]

                if self._current.voltage_c[i] != self._new.voltage_c[i]:
                    self._device.write(f"SOUR{i + 1}:VOLTC {self._new.voltage_c[i]}")
                    self._current.voltage_c[i] = self._new.voltage_c[i]

                if self._current.current_c[i] != self._new.current_c[i]:
                    self._device.write(f"SOUR{i + 1}:CURRC {self._new.current_c[i]}")
                    self._current.current_c[i] = self._new.current_c[i]

                if not self._current.is_diode_mode[i]:
                    if self._current.voltage_e[i] != self._new.voltage_e[i]:
                        self._device.write(f"SOUR{i + 1}:VOLTE {self._new.voltage_e[i]}")
                        self._current.voltage_e[i] = self._new.voltage_e[i]

                    if self._current.current_e[i] != self._new.current_e[i]:
                        self._device.write(f"SOUR{i + 1}:CURRE {self._new.current_e[i]}")
                        self._current.current_e[i] = self._new.current_e[i]

        except DeviceIOError as e:
            logger.error(f"Error occurred while updating device: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False

    def query_device_setup(self) -> None:
        logger.info("Querying device setup...")
        try:
            for i in range(CHANNEL_COUNT):
                self._current.is_disabled[i] = self._device.query(f"OUTP{i + 1}?") == "OFF"
                # TODO: doesn't exist yet
                # self._current_values.is_diode_mode[i] = self._device.query(f"MODE{i + 1}?") == "DIODE"
                # TODO: make this better
                self._current.is_high_range[i] = float(self._device.query(f"SOUR{i + 1}:CURR:RANG?")) > 1e-5

                self._current.voltage_c[i] = float(self._device.query(f"SOUR{i + 1}:VOLTC?"))
                self._current.current_c[i] = float(self._device.query(f"SOUR{i + 1}:CURRC?")) * 1e6
                self._current.voltage_e[i] = float(self._device.query(f"SOUR{i + 1}:VOLTE?"))
                self._current.current_e[i] = float(self._device.query(f"SOUR{i + 1}:CURRE?")) * 1e6

            self.setup_updated.emit(self._current)
        except DeviceIOError as e:
            logger.error(f"Error occurred while querying device setup: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False


class Device(ABC):
    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def write(self, command: str) -> None:
        pass

    @abstractmethod
    def query(self, command: str) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class DeviceDisconnectedError(Exception):
    pass


class DeviceConnectionError(Exception):
    pass


class DeviceIOError(Exception):
    pass



class RealDevice(Device):
    def __init__(self, ip: str) -> None:
        self._sock: socket.socket | None = None
        self._ip = ip
        self._port = 5025
        self._stop = threading.Event()
        self._timeout = 3  # seconds for socket operations
        self._buffer = b""

    def open(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            try:
                # Platform‑specific keep‑alive parameters (Linux / macOS)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 5)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            except (AttributeError, OSError) as e:
                raise DeviceIOError("TCP keep-alive settings not yet supported on Windows") from e

            sock.connect((self._ip, self._port))
            self._sock = sock
            logger.info(f"Connected to {self._ip}:{self._port}")
        except TimeoutError as e:
            raise DeviceConnectionError(f"Connection timeout to {self._ip}:{self._port}: {e}") from e
        except ConnectionRefusedError as e:
            raise DeviceConnectionError(f"Connection refused: {e}") from e
        except OSError as e:
            raise DeviceIOError(f"Socket error while opening device: {e}") from e

    def _send(self, data: bytes) -> None:
        if self._sock is None:
            raise RuntimeError("Device not initialized.")
        try:
            self._sock.sendall(data)
        except (TimeoutError, ConnectionResetError, BrokenPipeError) as e:
            raise DeviceDisconnectedError(f"Connection lost while sending: {e}") from e
        except OSError as e:
            raise DeviceIOError(f"Socket error during send: {e}") from e

    def _read_until(self, terminator: bytes = b"\n") -> bytes:
        if self._sock is None:
            raise RuntimeError("Device not initialized.")
        data = b""
        try:
            while True:
                if terminator in self._buffer:
                    pos = self._buffer.find(terminator) + len(terminator)
                    data, self._buffer = self._buffer[:pos], self._buffer[pos:]
                    return data
                
                chunk = self._sock.recv(4096)
                if not chunk:
                    raise DeviceDisconnectedError("Socket closed by remote while reading")
                self._buffer += chunk
        except TimeoutError as e:
            raise DeviceIOError("Read timeout - no data") from e
        except ConnectionResetError as e:
            raise DeviceDisconnectedError(f"Connection reset while reading: {e}") from e
        except OSError as e:
            raise DeviceIOError(f"Socket error during read: {e}") from e
        return data

    def write(self, command: str) -> None:
        """Send a command (appends newline)."""
        if self._sock is None:
            raise RuntimeError("Device not initialized.")
        try:
            cmd_bytes = (command + "\n").encode("ascii")
            logger.info(f"Sending: {command}")
            self._send(cmd_bytes)
        except (DeviceDisconnectedError, DeviceIOError):
            raise
        except Exception as e:
            raise DeviceIOError(f"Unexpected error while writing: {e}") from e

    def query(self, command: str) -> str:
        """Send a command and read the response (terminated by newline)."""
        if self._sock is None:
            raise RuntimeError("Device not initialized.")
        try:
            self.write(command)  # write also logs and handles exceptions
            response = self._read_until(b"\n")
            ret = response.decode("ascii").rstrip("\n")
            logger.info(f"Received: {ret}")
            return ret
        except (DeviceDisconnectedError, DeviceIOError):
            raise
        except Exception as e:
            raise DeviceIOError(f"Unexpected error during query: {e}") from e

    def close(self) -> None:
        """Close the socket and signal the stop event."""
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self._stop.set()

class DebugDevice(Device):
    def __init__(self, ip: str) -> None:
        self._ip = ip

    def open(self) -> None:
        return

    def write(self, command: str) -> None:
        print(f"DebugDevice({self._ip}): write({command})")
        return

    def query(self, command: str) -> str:
        print(f"DebugDevice({self._ip}): query({command})")
        if "MEAS" in command and "VOLT" in command:
            return str(random.uniform(-1200.0, -1))
        elif "MEAS" in command and "CURR" in command:
            return str(random.uniform(0.0, 1.0))
        raise RuntimeError("Unexpected query response.")

    def close(self) -> None:
        print(f"DebugDevice({self._ip}): close()")
