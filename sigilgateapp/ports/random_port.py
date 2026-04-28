from typing import Protocol


class RandomPort(Protocol):
    def uuid(self) -> str: ...
