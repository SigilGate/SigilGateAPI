from datetime import datetime, timezone

from sigilgateapp.domain.entities import DeviceUuid, NodeIp, Route
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.route_record import RouteRecord

_NS = "/sigilgate/routes/"


def _base(uuid: str) -> str:
    return f"{_NS}{uuid}/"


def domain_to_keys(route: Route) -> list[tuple[str, str]]:
    base = _base(route.uuid)
    return [
        (f"{base}core_ip", str(route.core_ip)),
        (f"{base}status", route.status.value),
        (f"{base}status_at", route.status_at.isoformat()),
    ]


def keys_to_record(uuid: str, data: dict[str, str]) -> RouteRecord:
    base = _base(uuid)
    return RouteRecord(
        uuid=uuid,
        core_ip=data.get(f"{base}core_ip"),
        status=data.get(f"{base}status"),
        status_at=data.get(f"{base}status_at"),
    )


def record_to_domain(record: RouteRecord) -> Result[Route, DomainError]:
    if record.core_ip is None:
        return Err(NotFound("Route", record.uuid))
    if record.status is None or record.status_at is None:
        return Err(ValidationError("Route", f"неполные данные для uuid={record.uuid}"))
    try:
        status = Status(record.status)
        status_at = datetime.fromisoformat(record.status_at)
        if status_at.tzinfo is None:
            status_at = status_at.replace(tzinfo=timezone.utc)
    except (ValueError, KeyError) as e:
        return Err(ValidationError("Route", str(e)))
    return Ok(Route(
        uuid=DeviceUuid(record.uuid),
        core_ip=NodeIp(record.core_ip),
        status=status,
        status_at=status_at,
    ))


def prefix_to_domain(uuid: str, data: dict[str, str]) -> Result[Route, DomainError]:
    record = keys_to_record(uuid, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
