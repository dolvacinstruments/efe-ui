import random
from enum import StrEnum

import pyvisa
from PySide6.QtCore import QMutex, QMutexLocker, QObject, QTimer, Signal, Slot
from pyvisa.resources import MessageBasedResource

from efe_ui.constants import CHANNEL_COUNT, VariableType

REFRESH_INTERVAL_MS = 200


class DeviceStatus(StrEnum):
    CONNECTED = "Connected"
    CANNOT_CONNECT = "Failed to connect"
    ERROR = "Error"


class Device(QObject):
    status_updated = Signal(DeviceStatus)
    variable_updated = Signal(VariableType, float, int)

    def __init__(self, ip: str) -> None:
        super().__init__()
        self._ip = ip
        self._is_diode_mode = [True] * CHANNEL_COUNT
        self._is_enabled = [False] * CHANNEL_COUNT

        self._device_mutex = QMutex()
        self._device: MessageBasedResource | DebugDevice | None = None

    def open(self) -> None:
        with QMutexLocker(self._device_mutex):
            # Debug code:
            self._device = DebugDevice(self._ip)
            self.status_updated.emit(DeviceStatus.CONNECTED)

            return
            rm = pyvisa.ResourceManager("@py")
            for _ in range(3):
                try:
                    self._device: MessageBasedResource = rm.open_resource(f"TCPIP0::{self._ip}::INSTR")  # ty:ignore[invalid-assignment]
                    self.status_updated.emit(DeviceStatus.CONNECTED)
                    self.start_loop()
                    return
                except pyvisa.VisaIOError:
                    continue
            self.status_updated.emit(DeviceStatus.CANNOT_CONNECT)

    @Slot()
    def start_loop(self) -> None:
        self.open()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_device)
        self.timer.start(REFRESH_INTERVAL_MS)

    @Slot(bool, int)
    def set_enabled(self, is_enabled: bool, channel: int) -> None:
        with QMutexLocker(self._device_mutex):
            if self._device is None:
                self.status_updated.emit(DeviceStatus.ERROR)
                return
            if is_enabled:
                self._device.write(f"OUTP{channel + 1} ON")
            else:
                self._device.write(f"OUTP{channel + 1} OFF")
            self._is_enabled[channel] = is_enabled

    @Slot(bool, int)
    def set_diode_mode(self, is_diode_mode: bool, channel: int) -> None:
        with QMutexLocker(self._device_mutex):
            if self._device is None:
                self.status_updated.emit(DeviceStatus.ERROR)
                return
            if is_diode_mode:
                self._device.write(f"FUNC{channel + 1} DIODE")
            else:
                self._device.write(f"FUNC{channel + 1} TRIODE")
            self._is_diode_mode[channel] = is_diode_mode

    @Slot(bool, int)
    def set_high_range(self, is_high_range: bool, channel: int) -> None:
        with QMutexLocker(self._device_mutex):
            if self._device is None:
                self.status_updated.emit(DeviceStatus.ERROR)
                return
            if is_high_range:
                self._device.write(f"RANGE{channel + 1} HIGH")
            else:
                self._device.write(f"RANGE{channel + 1} LOW")

    @Slot(int, VariableType, float)
    def set_value(self, variable_type: VariableType, value: float, channel: int) -> None:
        with QMutexLocker(self._device_mutex):
            if self._device is None:
                self.status_updated.emit(DeviceStatus.ERROR)
                return
            if variable_type == VariableType.VOLTAGE_C:
                self._device.write(f"SOUR{channel + 1}:VOLTC {value}")
            elif variable_type == VariableType.CURRENT:
                self._device.write(f"SOUR{channel + 1}:CURR {value}")
            elif variable_type == VariableType.VOLTAGE_CE:
                self._device.write(f"SOUR{channel + 1}:VOLTCE {value}")
            elif variable_type == VariableType.CURRENT_C:
                self._device.write(f"SOUR{channel + 1}:CURRC {value}")

    @Slot()
    def poll_device(self) -> None:
        with QMutexLocker(self._device_mutex):
            if self._device is None:
                self.status_updated.emit(DeviceStatus.ERROR)
                return
            for i in range(CHANNEL_COUNT):
                if not self._is_enabled[i]:
                    continue
                try:
                    vc = float(self._device.query(f"MEAS{i + 1}:VOLTC?"))
                    self.variable_updated.emit(VariableType.VOLTAGE_C, vc, i)
                    curr = float(self._device.query(f"MEAS{i + 1}:CURR?"))
                    self.variable_updated.emit(VariableType.CURRENT, curr, i)

                    if not self._is_diode_mode[i]:
                        vce = float(self._device.query(f"MEAS{i + 1}:VOLTCE?"))
                        self.variable_updated.emit(VariableType.VOLTAGE_CE, vce, i)

                except pyvisa.VisaIOError:
                    self.status_updated.emit(DeviceStatus.ERROR)


class DebugDevice:
    def __init__(self, ip: str) -> None:
        self._ip = ip

    def write(self, command: str) -> None:
        print(f"DebugDevice({self._ip}): write({command})")

    def query(self, command: str) -> str:
        print(f"DebugDevice({self._ip}): query({command})")
        if "MEAS" in command and "VOLT" in command:
            return str(random.uniform(-1200.0, -1))
        elif "MEAS" in command and "CURR" in command:
            return str(random.uniform(0.0, 1.0))
        return "0.0"
