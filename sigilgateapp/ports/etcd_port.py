from typing import Protocol


class EtcdPort(Protocol):
    def get(self, key: str) -> str | None: ...

    def put(self, key: str, value: str) -> None: ...

    def delete(self, key: str) -> None: ...

    def prefix_scan(self, prefix: str) -> dict[str, str]: ...

    def txn(self, ops: list[tuple[str, str | None]]) -> None:
        # ops: (key, value) — value=None означает DELETE
        ...

    def compare_and_swap(self, key: str, expected: str | None, value: str) -> bool:
        # Атомарно: если key == expected, записать value. True = успех.
        # expected=None: ключ не должен существовать.
        ...
