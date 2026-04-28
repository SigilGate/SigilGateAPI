from dataclasses import dataclass


@dataclass(frozen=True)
class RouteRecord:
    uuid: str
    core_ip: str | None = None
    status: str | None = None
    status_at: str | None = None
