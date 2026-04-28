from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserRecord:
    id: str
    username: str | None = None
    status: str | None = None
    status_at: str | None = None
    created: str | None = None
    hash_telegram_id: str | None = None
    core_nodes: frozenset[str] = field(default_factory=frozenset)
