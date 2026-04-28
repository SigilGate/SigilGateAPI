from sigilgateapp.domain.entities import PubId, PublicUser
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.public_user_record import PublicUserRecord

_NS = "/public/users/"


def _base(pub_id: int) -> str:
    return f"{_NS}{pub_id}/"


def domain_to_keys(user: PublicUser) -> list[tuple[str, str]]:
    base = _base(user.pub_id)
    keys: list[tuple[str, str]] = [
        (f"{base}username", user.username),
        (f"{base}hash_telegram_id", user.hash_telegram_id),
    ]
    if user.telegram is not None:
        keys.append((f"{base}telegram", user.telegram))
    if user.email is not None:
        keys.append((f"{base}email", user.email))
    return keys


def keys_to_record(pub_id: int, data: dict[str, str]) -> PublicUserRecord:
    base = _base(pub_id)
    return PublicUserRecord(
        pub_id=str(pub_id),
        username=data.get(f"{base}username"),
        hash_telegram_id=data.get(f"{base}hash_telegram_id"),
        telegram=data.get(f"{base}telegram"),
        email=data.get(f"{base}email"),
    )


def record_to_domain(record: PublicUserRecord) -> Result[PublicUser, DomainError]:
    if record.username is None or record.hash_telegram_id is None:
        return Err(NotFound("PublicUser", record.pub_id))
    try:
        pub_id = PubId(int(record.pub_id))
    except ValueError as e:
        return Err(ValidationError("PublicUser", str(e)))
    return Ok(PublicUser(
        pub_id=pub_id,
        username=record.username,
        hash_telegram_id=record.hash_telegram_id,
        telegram=record.telegram,
        email=record.email,
    ))


def prefix_to_domain(pub_id: int, data: dict[str, str]) -> Result[PublicUser, DomainError]:
    record = keys_to_record(pub_id, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
