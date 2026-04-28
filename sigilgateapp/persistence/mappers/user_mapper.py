from datetime import datetime, timezone

from sigilgateapp.domain.entities import NodeIp, User, UserId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.user_record import UserRecord

_NS = "/sigilgate/users/"


def _base(user_id: int) -> str:
    return f"{_NS}{user_id}/"


def domain_to_keys(user: User) -> list[tuple[str, str]]:
    base = _base(user.id)
    keys: list[tuple[str, str]] = [
        (f"{base}username", user.username),
        (f"{base}status", user.status.value),
        (f"{base}status_at", user.status_at.isoformat()),
        (f"{base}created", user.created.isoformat()),
    ]
    if user.hash_telegram_id is not None:
        keys.append((f"{base}hash_telegram_id", user.hash_telegram_id))
    for ip in user.core_nodes:
        keys.append((f"{base}core_nodes/{ip}", ""))
    return keys


def keys_to_record(user_id: int, data: dict[str, str]) -> UserRecord:
    base = _base(user_id)
    core_nodes_prefix = f"{base}core_nodes/"
    core_nodes = frozenset(
        key[len(core_nodes_prefix):]
        for key in data
        if key.startswith(core_nodes_prefix)
    )
    return UserRecord(
        id=str(user_id),
        username=data.get(f"{base}username"),
        status=data.get(f"{base}status"),
        status_at=data.get(f"{base}status_at"),
        created=data.get(f"{base}created"),
        hash_telegram_id=data.get(f"{base}hash_telegram_id"),
        core_nodes=core_nodes,
    )


def record_to_domain(record: UserRecord) -> Result[User, DomainError]:
    if record.username is None:
        return Err(NotFound("User", record.id))
    if record.status is None or record.status_at is None or record.created is None:
        return Err(ValidationError("User", f"неполные данные для id={record.id}"))
    try:
        status = Status(record.status)
        status_at = datetime.fromisoformat(record.status_at)
        if status_at.tzinfo is None:
            status_at = status_at.replace(tzinfo=timezone.utc)
        created = datetime.fromisoformat(record.created)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
    except (ValueError, KeyError) as e:
        return Err(ValidationError("User", str(e)))
    return Ok(User(
        id=UserId(int(record.id)),
        username=record.username,
        status=status,
        status_at=status_at,
        created=created,
        hash_telegram_id=record.hash_telegram_id,
        core_nodes=frozenset(NodeIp(ip) for ip in record.core_nodes),
    ))


def prefix_to_domain(user_id: int, data: dict[str, str]) -> Result[User, DomainError]:
    record = keys_to_record(user_id, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
