from dataclasses import dataclass


@dataclass(frozen=True)
class JoinTokenRecord:
    token: str
    created_at: str | None = None
    expires_at: str | None = None
    used: str | None = None  # "true" | "false"
    cell_domain: str | None = None
    node_number: str | None = None
    assigned_domain: str | None = None
