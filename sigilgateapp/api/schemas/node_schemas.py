from pydantic import BaseModel

from sigilgateapp.domain.enums import NodeRole, Status


class RegisterNodeRequest(BaseModel):
    ip: str
    role: NodeRole
    domain: str | None = None
    cell_domain: str | None = None
    node_number: int | None = None
    uuid: str | None = None
    client_service_name: str | None = None
    core_service_name: str | None = None


class JoinNodeRequest(BaseModel):
    join_token: str
    ip: str
    uuid: str
    core_service_name: str


class SetNodeStatusRequest(BaseModel):
    status: Status
