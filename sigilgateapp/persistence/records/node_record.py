from dataclasses import dataclass


@dataclass(frozen=True)
class NodeRecord:
    ip: str
    role: str | None = None
    status: str | None = None
    status_at: str | None = None
    domain: str | None = None
    cell_domain: str | None = None
    node_number: str | None = None
    uuid: str | None = None
    client_service_name: str | None = None
    core_service_name: str | None = None
