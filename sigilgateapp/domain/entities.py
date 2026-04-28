from dataclasses import dataclass, field
from datetime import datetime
from typing import NewType

from sigilgateapp.domain.enums import NodeRole, Status

NodeIp = NewType("NodeIp", str)
UserId = NewType("UserId", int)
DeviceUuid = NewType("DeviceUuid", str)
CellDomain = NewType("CellDomain", str)
PubId = NewType("PubId", int)
TokenId = NewType("TokenId", str)
AppealId = NewType("AppealId", str)


@dataclass(frozen=True)
class User:
    id: UserId
    username: str
    status: Status
    status_at: datetime
    created: datetime
    hash_telegram_id: str | None = None
    core_nodes: frozenset[NodeIp] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Device:
    uuid: DeviceUuid
    user_id: UserId
    name: str
    status: Status
    status_at: datetime
    created: datetime
    core_node: NodeIp | None = None


@dataclass(frozen=True)
class Node:
    ip: NodeIp
    role: NodeRole
    status: Status
    status_at: datetime
    domain: str | None = None
    cell_domain: CellDomain | None = None
    node_number: int | None = None
    uuid: str | None = None
    client_service_name: str | None = None
    core_service_name: str | None = None


@dataclass(frozen=True)
class Route:
    uuid: DeviceUuid
    core_ip: NodeIp
    status: Status
    status_at: datetime


@dataclass(frozen=True)
class PublicUser:
    pub_id: PubId
    username: str
    hash_telegram_id: str
    telegram: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class Message:
    from_pub_id: PubId
    text: str
    ts: datetime


@dataclass(frozen=True)
class Appeal:
    appeal_id: AppealId
    pub_id: PubId
    subject: str
    status: Status
    status_at: datetime
    created: datetime
    messages: tuple[Message, ...] = field(default_factory=tuple)
    admin_pub_id: PubId | None = None


@dataclass(frozen=True)
class JoinToken:
    token: str
    created_at: datetime
    expires_at: datetime
    used: bool
    cell_domain: str
    node_number: int
    assigned_domain: str


@dataclass(frozen=True)
class ApiToken:
    token_id: TokenId
    name: str
    token_hash: str
    created: datetime
    active: bool
    last_used_at: datetime | None = None
