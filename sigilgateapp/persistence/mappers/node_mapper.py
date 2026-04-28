from datetime import datetime, timezone

from sigilgateapp.domain.entities import CellDomain, Node, NodeIp
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.node_record import NodeRecord

_NS = "/sigilgate/nodes/"


def _base(ip: str) -> str:
    return f"{_NS}{ip}/"


def domain_to_keys(node: Node) -> list[tuple[str, str]]:
    base = _base(node.ip)
    keys: list[tuple[str, str]] = [
        (f"{base}role", node.role.value),
        (f"{base}status", node.status.value),
        (f"{base}status_at", node.status_at.isoformat()),
    ]
    if node.domain is not None:
        keys.append((f"{base}domain", node.domain))
    if node.cell_domain is not None:
        keys.append((f"{base}cell_domain", node.cell_domain))
    if node.node_number is not None:
        keys.append((f"{base}node_number", str(node.node_number)))
    if node.uuid is not None:
        keys.append((f"{base}uuid", node.uuid))
    if node.client_service_name is not None:
        keys.append((f"{base}client_service_name", node.client_service_name))
    if node.core_service_name is not None:
        keys.append((f"{base}core_service_name", node.core_service_name))
    return keys


def keys_to_record(ip: str, data: dict[str, str]) -> NodeRecord:
    base = _base(ip)
    return NodeRecord(
        ip=ip,
        role=data.get(f"{base}role"),
        status=data.get(f"{base}status"),
        status_at=data.get(f"{base}status_at"),
        domain=data.get(f"{base}domain"),
        cell_domain=data.get(f"{base}cell_domain"),
        node_number=data.get(f"{base}node_number"),
        uuid=data.get(f"{base}uuid"),
        client_service_name=data.get(f"{base}client_service_name"),
        core_service_name=data.get(f"{base}core_service_name"),
    )


def record_to_domain(record: NodeRecord) -> Result[Node, DomainError]:
    if record.role is None:
        return Err(NotFound("Node", record.ip))
    if record.status is None or record.status_at is None:
        return Err(ValidationError("Node", f"неполные данные для ip={record.ip}"))
    try:
        role = NodeRole(record.role)
        status = Status(record.status)
        status_at = datetime.fromisoformat(record.status_at)
        if status_at.tzinfo is None:
            status_at = status_at.replace(tzinfo=timezone.utc)
        node_number = int(record.node_number) if record.node_number is not None else None
    except (ValueError, KeyError) as e:
        return Err(ValidationError("Node", str(e)))
    return Ok(Node(
        ip=NodeIp(record.ip),
        role=role,
        status=status,
        status_at=status_at,
        domain=record.domain,
        cell_domain=CellDomain(record.cell_domain) if record.cell_domain is not None else None,
        node_number=node_number,
        uuid=record.uuid,
        client_service_name=record.client_service_name,
        core_service_name=record.core_service_name,
    ))


def prefix_to_domain(ip: str, data: dict[str, str]) -> Result[Node, DomainError]:
    record = keys_to_record(ip, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
