import socket
import struct

from PySide6.QtCore import QObject, Slot

LOG_CONTENT_MAX_LEN = 100
HEADER_FORMAT = "<I Q b"  # Little-endian: uint32 (id), uint64 (timestamp), char (level)
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

                device_id, timestamp_raw, level_raw = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])

                timestamp = timestamp_raw / 1_000_000
                level_str = LOG_LEVEL_MAP.get(level_raw, f"UNKNOWN({level_raw})")

                content_raw = data[HEADER_SIZE:]
                content_str = list(x.decode("utf-8", errors="replace").strip() for x in content_raw.split(b"\x00"))

                if len(content_str) <= 1:
                    print(f"[{addr[0]}] Received log with no content")
                    continue
                else:
                    print(f"[{timestamp:.3f}][D:{device_id:x}][{level_str}][{content_str[0]}] {content_str[1]}")
