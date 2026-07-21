import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel, RootModel


class DeviceConfig(BaseModel):
    name: str
    ip: str


class DevicesConfig(RootModel[list[DeviceConfig]]):
    pass

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        with open(file_path, encoding="utf-8") as file:
            raw = json.load(file)
        return cls.model_validate(raw)

    @classmethod
    def from_lists(cls, names: list[str], ips: list[str]) -> Self:
        if len(names) != len(ips):
            raise ValueError("Names and IPs lists must have the same length.")
        devices = [DeviceConfig(name=name, ip=ip) for name, ip in zip(names, ips, strict=False)]
        return cls.model_validate(devices)

    def to_file(self, file_path: Path) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(self.model_dump(), file, indent=4)
