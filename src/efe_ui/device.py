import logging
import math
import random
import socket
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from efe_ui.constants import CHANNEL_COUNT, VariableType
from efe_ui.number_widget import Value

logger = logging.getLogger(__name__)


REFRESH_INTERVAL_MS = 200


class DeviceStatusKind(StrEnum):
    OK = "OK"
    SYNCING = "Syncing"
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

    @classmethod
    def syncing(cls) -> Self:
        return cls(kind=DeviceStatusKind.SYNCING, message="Syncing...")


@dataclass
class DeviceSetup:
    is_disabled: list[bool | None]
    is_high_range: list[bool | None]

    voltage_c: list[float | None]
    current_c: list[float | None]
    voltage_e: list[float | None]
    current_e: list[float | None]

    def __init__(self) -> None:
        self.is_disabled = [None] * CHANNEL_COUNT
        self.is_high_range = [None] * CHANNEL_COUNT

        self.voltage_c = [None] * CHANNEL_COUNT
        self.current_c = [None] * CHANNEL_COUNT
        self.voltage_e = [None] * CHANNEL_COUNT
        self.current_e = [None] * CHANNEL_COUNT

    @classmethod
    def zeroed(cls) -> Self:
        setup = cls()
        setup.is_disabled = [True] * CHANNEL_COUNT
        setup.is_high_range = [True] * CHANNEL_COUNT

        setup.voltage_c = [-5.0] * CHANNEL_COUNT
        setup.current_c = [0.0] * CHANNEL_COUNT
        setup.voltage_e = [-5.0] * CHANNEL_COUNT
        setup.current_e = [-100e-6] * CHANNEL_COUNT

        return setup

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DeviceSetup):
            return NotImplemented
        return (
            self.is_disabled == other.is_disabled
            and self.is_high_range == other.is_high_range
            and all(float_compare(a, b) for a, b in zip(self.voltage_c, other.voltage_c, strict=True))
            and all(float_compare(a, b) for a, b in zip(self.current_c, other.current_c, strict=True))
            and all(float_compare(a, b) for a, b in zip(self.voltage_e, other.voltage_e, strict=True))
            and all(float_compare(a, b) for a, b in zip(self.current_e, other.current_e, strict=True))
        )


class CathodeState(StrEnum):
    CV = "CV"
    CC = "CC"
    OFF = "OFF"
    UNSTABLE = "UNSTABLE"
    LOCKOUT = "LOCKOUT"
    ERROR = "ERROR"


class ExtractionState(StrEnum):
    CV = "CV"
    CC = "CC"
    EKV = "KCV"
    OFF = "OFF"
    UNSTABLE = "UNSTABLE"
    LOCKOUT = "LOCKOUT"
    ERROR = "ERROR"


@dataclass
class DeviceMeasured:
    voltage_c: list[Value]
    voltage_e: list[Value]
    current: list[Value]

    state_c: list[CathodeState]
    state_e: list[ExtractionState]

    def __init__(self) -> None:
        self.voltage_c = [Value.invalid()] * CHANNEL_COUNT
        self.voltage_e = [Value.invalid()] * CHANNEL_COUNT
        self.current = [Value.invalid()] * CHANNEL_COUNT
        self.state_c = [CathodeState.UNSTABLE] * CHANNEL_COUNT
        self.state_e = [ExtractionState.UNSTABLE] * CHANNEL_COUNT


class TickWorker(QObject):
    def __init__(self, tick_callback: Callable[[], None]) -> None:
        super().__init__()
        self.tick_callback = tick_callback
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._tick)

    def start(self) -> None:
        self.timer.start(REFRESH_INTERVAL_MS)
        pass

    def _tick(self) -> None:
        start_time = time.time()

        try:
            self.tick_callback()
        except Exception as e:
            logger.error(e, exc_info=True)

        elapsed = (time.time() - start_time) * 1000
        delay = int(max(0, REFRESH_INTERVAL_MS - elapsed))
        self.timer.start(delay)


class EFE(QObject):
    force_disable = Signal()
    status_updated = Signal(DeviceStatus)
    measured_updated = Signal(DeviceMeasured)

    def __init__(self, ip: str) -> None:
        super().__init__()
        self._setup = DeviceSetup()
        self._pending_setup = DeviceSetup.zeroed()

        self._device = RealDevice(ip)
        self._device_connected = False
        self._worker = None

    @Slot()
    def start_loop(self) -> None:
        self._worker = TickWorker(self.tick)
        self._worker.start()

    @Slot()
    def tick(self) -> None:
        if self._device_connected:
            self.update_device()
            self.ensure_setup_synced()
            self.poll_device()
        else:
            logger.info("Device not connected. Attempting to connect...")
            self.connect_device()

    @Slot()
    def stop_worker(self) -> None:
        if self._worker is None:
            raise RuntimeError("Worker is None when it should not be.")
        self._worker.timer.stop()
        if self._device is not None:
            self._device.close()
        self.thread().quit()

    @Slot(int, bool)
    def set_disabled(self, channel: int, is_disabled: bool) -> None:
        self._pending_setup.is_disabled[channel] = is_disabled

    @Slot(int, bool)
    def set_high_range(self, channel: int, is_high_range: bool) -> None:
        self._pending_setup.is_high_range[channel] = is_high_range

    @Slot(int, VariableType, float)
    def set_value(self, channel: int, variable_type: VariableType, value: float) -> None:
        if variable_type == VariableType.VOLTAGE_C:
            self._pending_setup.voltage_c[channel] = value
        elif variable_type == VariableType.CURRENT_C:
            self._pending_setup.current_c[channel] = value / 1e6
        elif variable_type == VariableType.VOLTAGE_E:
            self._pending_setup.voltage_e[channel] = value
        elif variable_type == VariableType.CURRENT_E:
            self._pending_setup.current_e[channel] = value / 1e6

    def connect_device(self) -> None:
        try:
            self._device.open()
            self._setup = DeviceSetup()
            self._device_connected = True
            self.status_updated.emit(DeviceStatus.ok())
            self.force_disable.emit()
        except DeviceConnectionError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.CONNECTION_ERROR, str(e)))

    def poll_device(self) -> None:
        try:
            measured = DeviceMeasured()
            response = self._device.query("MEAS:ALL?")
            raw_values = response.split(",")
            if len(raw_values) == CHANNEL_COUNT * 3:
                for i in range(CHANNEL_COUNT):
                    measured.current[i] = Value(float(raw_values.pop(0)) * 1e6)  # microamps
                    measured.voltage_c[i] = Value(float(raw_values.pop(0)))
                    measured.voltage_e[i] = Value(float(raw_values.pop(0)))
                    measured.state_c[i] = CathodeState.UNSTABLE  # Placeholder
                    measured.state_e[i] = ExtractionState.UNSTABLE  # Placeholder
            elif len(raw_values) == CHANNEL_COUNT * 5:
                for i in range(CHANNEL_COUNT):
                    measured.current[i] = Value(float(raw_values.pop(0)) * 1e6)  # microamps
                    measured.voltage_c[i] = Value(float(raw_values.pop(0)))
                    measured.voltage_e[i] = Value(float(raw_values.pop(0)))
                    measured.state_c[i] = CathodeState(raw_values.pop(0).strip())
                    measured.state_e[i] = ExtractionState(raw_values.pop(0).strip())
            else:
                raise RuntimeError(f"Unexpected number of values in response: {len(raw_values)}")

            self.measured_updated.emit(measured)
        except DeviceIOError as e:
            logger.error(f"Error occurred while polling device: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False

    def update_device(self) -> None:
        try:
            changes_occured = False
            for i in range(CHANNEL_COUNT):
                if self._setup.is_disabled[i] != self._pending_setup.is_disabled[i]:
                    if self._pending_setup.is_disabled[i]:
                        self._device.write(f"OUTP{i + 1} OFF")
                    else:
                        self._device.write(f"OUTP{i + 1} ON")
                    changes_occured = True
                if self._setup.is_high_range[i] != self._pending_setup.is_high_range[i]:
                    if self._pending_setup.is_high_range[i]:
                        self._device.write(f"SOUR{i + 1}:CURR:RANG 1e-4")
                    else:
                        self._device.write(f"SOUR{i + 1}:CURR:RANG 1e-6")
                    changes_occured = True
                if not float_compare(self._setup.voltage_c[i], self._pending_setup.voltage_c[i]):
                    self._device.write(f"SOUR{i + 1}:VOLTC {self._pending_setup.voltage_c[i]}")
                    changes_occured = True
                if not float_compare(self._setup.current_c[i], self._pending_setup.current_c[i]):
                    self._device.write(f"SOUR{i + 1}:CURRC {self._pending_setup.current_c[i]}")
                    changes_occured = True
                if not float_compare(self._setup.voltage_e[i], self._pending_setup.voltage_e[i]):
                    self._device.write(f"SOUR{i + 1}:VOLTE {self._pending_setup.voltage_e[i]}")
                    changes_occured = True
                if not float_compare(self._setup.current_e[i], self._pending_setup.current_e[i]):
                    self._device.write(f"SOUR{i + 1}:CURRE {self._pending_setup.current_e[i]}")
                    changes_occured = True
            if changes_occured:
                self.status_updated.emit(DeviceStatus.syncing())

        except DeviceIOError as e:
            logger.error(f"Error occurred while updating device: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False

    def ensure_setup_synced(self) -> None:
        try:
            check_needed = self._setup != self._pending_setup

            for i in range(CHANNEL_COUNT):
                if self._setup.is_disabled[i] != self._pending_setup.is_disabled[i]:
                    ret = self._device.query(f"OUTP{i + 1}?")
                    self._setup.is_disabled[i] = int(ret.strip()) == 0
                if self._setup.is_high_range[i] != self._pending_setup.is_high_range[i]:
                    ret = self._device.query(f"SOUR{i + 1}:CURR:RANG?")
                    self._setup.is_high_range[i] = float(ret.strip()) == 1e-4
                if not float_compare(self._setup.voltage_c[i], self._pending_setup.voltage_c[i]):
                    ret = self._device.query(f"SOUR{i + 1}:VOLTC?")
                    self._setup.voltage_c[i] = float(ret.strip())
                if not float_compare(self._setup.current_c[i], self._pending_setup.current_c[i]):
                    ret = self._device.query(f"SOUR{i + 1}:CURRC?")
                    self._setup.current_c[i] = float(ret.strip())
                if not float_compare(self._setup.voltage_e[i], self._pending_setup.voltage_e[i]):
                    ret = self._device.query(f"SOUR{i + 1}:VOLTE?")
                    self._setup.voltage_e[i] = float(ret.strip())
                if not float_compare(self._setup.current_e[i], self._pending_setup.current_e[i]):
                    ret = self._device.query(f"SOUR{i + 1}:CURRE?")
                    self._setup.current_e[i] = float(ret.strip())

            if check_needed and self._setup == self._pending_setup:
                self.status_updated.emit(DeviceStatus.ok())

        except DeviceIOError as e:
            logger.error(f"Error occurred while querying device state: {e}")
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.IO_ERROR, str(e)))
        except DeviceDisconnectedError as e:
            self.status_updated.emit(DeviceStatus(DeviceStatusKind.DISCONNECTED, str(e)))
            self._device_connected = False


def float_compare(a: float | None, b: float | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return math.isclose(a, b)


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
            raise DeviceConnectionError(e) from e

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
            raise DeviceDisconnectedError("Read timeout - no data") from e  # decide how to handle
        except ConnectionResetError as e:
            raise DeviceDisconnectedError(f"Connection reset while reading: {e}") from e
        except OSError as e:
            raise DeviceIOError(f"Socket error during read: {e}") from e

    def write(self, command: str) -> None:
        """Send a command (appends newline)."""
        if self._sock is None:
            raise RuntimeError("Device not initialized.")
        try:
            cmd_bytes = (command + "\n").encode("ascii")
            logger.info(f"[{self._ip}] Sending: {command}")
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
            logger.info(f"[{self._ip}] Received: {ret}")
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
        elif "MEAS:ALL?" in command:
            values = []
            for _ in range(CHANNEL_COUNT):
                values.append(str(random.uniform(-1.0e-6, 0.0)))  # current
                values.append(str(random.uniform(-1200.0, -1.0)))  # voltage_c
                values.append(str(random.uniform(-1200.0, -1.0)))  # voltage_e
            return ",".join(values)
        raise RuntimeError("Unexpected query response.")

    def close(self) -> None:
        print(f"DebugDevice({self._ip}): close()")
