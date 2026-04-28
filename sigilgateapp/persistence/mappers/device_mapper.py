from datetime import datetime, timezone

from sigilgateapp.domain.entities import Device, DeviceUuid, NodeIp, UserId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.device_record import DeviceRecord

_USER_NS = "/sigilgate/users/"


def _base(user_id: int, uuid: str) -> str:
    return f"{_USER_NS}{user_id}/devices/{uuid}/"


def domain_to_keys(device: Device) -> list[tuple[str, str]]:
    base = _base(device.user_id, device.uuid)
    keys: list[tuple[str, str]] = [
        # etcd-ключ "device" соответствует domain-полю "name"
        (f"{base}device", device.name),
        (f"{base}status", device.status.value),
        (f"{base}status_at", device.status_at.isoformat()),
        (f"{base}created", device.created.isoformat()),
    ]
    if device.core_node is not None:
        keys.append((f"{base}core_node", str(device.core_node)))
    return keys


def keys_to_record(user_id: int, uuid: str, data: dict[str, str]) -> DeviceRecord:
    base = _base(user_id, uuid)
    return DeviceRecord(
        uuid=uuid,
        user_id=str(user_id),
        device=data.get(f"{base}device"),
        status=data.get(f"{base}status"),
        status_at=data.get(f"{base}status_at"),
        created=data.get(f"{base}created"),
        core_node=data.get(f"{base}core_node"),
    )


def record_to_domain(record: DeviceRecord) -> Result[Device, DomainError]:
    if record.device is None:
        return Err(NotFound("Device", record.uuid))
    if record.status is None or record.status_at is None or record.created is None:
        return Err(ValidationError("Device", f"неполные данные для uuid={record.uuid}"))
    try:
        status = Status(record.status)
        status_at = datetime.fromisoformat(record.status_at)
        if status_at.tzinfo is None:
            status_at = status_at.replace(tzinfo=timezone.utc)
        created = datetime.fromisoformat(record.created)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
    except (ValueError, KeyError) as e:
        return Err(ValidationError("Device", str(e)))
    return Ok(Device(
        uuid=DeviceUuid(record.uuid),
        user_id=UserId(int(record.user_id)),
        name=record.device,
        status=status,
        status_at=status_at,
        created=created,
        core_node=NodeIp(record.core_node) if record.core_node else None,
    ))


def prefix_to_domain(user_id: int, uuid: str, data: dict[str, str]) -> Result[Device, DomainError]:
    record = keys_to_record(user_id, uuid, data)
    return record_to_domain(record)


def devices_prefix(user_id: int) -> str:
    return f"{_USER_NS}{user_id}/devices/"
