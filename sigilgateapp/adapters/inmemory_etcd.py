class InMemoryEtcd:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def put(self, key: str, value: str) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def prefix_scan(self, prefix: str) -> dict[str, str]:
        return {k: v for k, v in self._store.items() if k.startswith(prefix)}

    def txn(self, ops: list[tuple[str, str | None]]) -> None:
        for key, value in ops:
            if value is None:
                self._store.pop(key, None)
            else:
                self._store[key] = value

    def compare_and_swap(self, key: str, expected: str | None, value: str) -> bool:
        if self._store.get(key) != expected:
            return False
        self._store[key] = value
        return True
