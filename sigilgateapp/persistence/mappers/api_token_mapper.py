from datetime import datetime, timezone

from sigilgateapp.domain.entities import ApiToken, TokenId
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.api_token_record import ApiTokenRecord

_NS = "/sigilgate/api_tokens/"


def _base(token_id: str) -> str:
    return f"{_NS}{token_id}/"


def domain_to_keys(token: ApiToken) -> list[tuple[str, str]]:
    base = _base(token.token_id)
    keys: list[tuple[str, str]] = [
        (f"{base}name", token.name),
        (f"{base}token_hash", token.token_hash),
        (f"{base}created", token.created.isoformat()),
        (f"{base}active", "true" if token.active else "false"),
    ]
    if token.last_used_at is not None:
        keys.append((f"{base}last_used_at", token.last_used_at.isoformat()))
    return keys


def keys_to_record(token_id: str, data: dict[str, str]) -> ApiTokenRecord:
    base = _base(token_id)
    return ApiTokenRecord(
        token_id=token_id,
        name=data.get(f"{base}name"),
        token_hash=data.get(f"{base}token_hash"),
        created=data.get(f"{base}created"),
        active=data.get(f"{base}active"),
        last_used_at=data.get(f"{base}last_used_at"),
    )


def record_to_domain(record: ApiTokenRecord) -> Result[ApiToken, DomainError]:
    if record.name is None:
        return Err(NotFound("ApiToken", record.token_id))
    if record.token_hash is None or record.created is None or record.active is None:
        return Err(ValidationError("ApiToken", f"неполные данные для token_id={record.token_id}"))
    try:
        created = datetime.fromisoformat(record.created)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        last_used_at: datetime | None = None
        if record.last_used_at is not None:
            last_used_at = datetime.fromisoformat(record.last_used_at)
            if last_used_at.tzinfo is None:
                last_used_at = last_used_at.replace(tzinfo=timezone.utc)
        active = record.active == "true"
    except ValueError as e:
        return Err(ValidationError("ApiToken", str(e)))
    return Ok(ApiToken(
        token_id=TokenId(record.token_id),
        name=record.name,
        token_hash=record.token_hash,
        created=created,
        active=active,
        last_used_at=last_used_at,
    ))


def prefix_to_domain(token_id: str, data: dict[str, str]) -> Result[ApiToken, DomainError]:
    record = keys_to_record(token_id, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
