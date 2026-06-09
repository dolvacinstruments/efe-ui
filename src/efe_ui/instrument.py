import pyvisa


class Instrument:
    def __init__(self) -> None:
        self.rm: pyvisa.ResourceManager | None = None
        self.resource: pyvisa.resources.MessageBasedResource | None = None
        self._connected: bool = False
        self._address: str = ""

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def address(self) -> str:
        return self._address

    def connect(self, host: str, port: int = 5025, timeout: int = 5000) -> None:
        self.rm = pyvisa.ResourceManager("@py")
        resource_string = f"TCPIP0::{host}::{port}::SOCKET"
        self.resource = self.rm.open_resource(
            resource_string,
            read_termination="\n",
            write_termination="\n",
            timeout=timeout,
        )
        self._address = host
        self._connected = True

    def disconnect(self) -> None:
        if self.resource is not None:
            self.resource.close()
        if self.rm is not None:
            self.rm.close()
        self.resource = None
        self.rm = None
        self._connected = False

    def write(self, command: str) -> int:
        if not self._connected or self.resource is None:
            raise ConnectionError("Not connected to an instrument")
        return self.resource.write(command)

    def query(self, command: str) -> str:
        if not self._connected or self.resource is None:
            raise ConnectionError("Not connected to an instrument")
        return self.resource.query(command).strip()

    def read(self) -> str:
        if not self._connected or self.resource is None:
            raise ConnectionError("Not connected to an instrument")
        return self.resource.read().strip()

    def ask_for_identity(self) -> str:
        return self.query("*IDN?")
