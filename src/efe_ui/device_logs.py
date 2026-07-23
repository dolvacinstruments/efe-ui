import socket
import struct

from PySide6.QtCore import QObject, Slot

LOG_CONTENT_MAX_LEN = 100
HEADER_FORMAT = "<I Q I"  # Little-endian: uint32 (id), uint64 (timestamp), uint32 (level)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
BUFFER_SIZE = HEADER_SIZE + LOG_CONTENT_MAX_LEN

# Map C log level enum integers to readable labels
LOG_LEVEL_MAP = {
    0: "DEBUG",
    1: "INFO",
    2: "WARN",
    3: "ERROR",
    4: "NONE",
}

HOST = "0.0.0.0"
PORT = 8888


class DeviceLogs(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    @Slot()
    def loop(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((HOST, PORT))
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if len(data) < HEADER_SIZE:
                    print(f"[{addr[0]}] Received truncated packet ({len(data)} bytes)")
                    continue

                device_id, timestamp, level_raw = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
                level_str = LOG_LEVEL_MAP.get(level_raw, f"UNKNOWN({level_raw})")

                raw_content = data[HEADER_SIZE:]
                content_str = raw_content.split(b"\x00")[0].decode("utf-8", errors="replace").strip()

                print(f"[{timestamp}] [Device: {device_id}] [{level_str}]: {content_str}")
