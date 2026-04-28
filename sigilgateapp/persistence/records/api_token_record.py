from dataclasses import dataclass


@dataclass(frozen=True)
class ApiTokenRecord:
    token_id: str
    name: str | None = None
    token_hash: str | None = None
    created: str | None = None
    active: str | None = None  # "true" | "false"
    last_used_at: str | None = None
