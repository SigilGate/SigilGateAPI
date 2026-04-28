from datetime import datetime, timezone

from sigilgateapp.domain.entities import JoinToken
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.join_token_record import JoinTokenRecord

_NS = "/sigilgate/tokens/join/"


def _base(token: str) -> str:
    return f"{_NS}{token}/"


def domain_to_keys(token: JoinToken) -> list[tuple[str, str]]:
    base = _base(token.token)
    return [
        (f"{base}created_at", token.created_at.isoformat()),
        (f"{base}expires_at", token.expires_at.isoformat()),
        (f"{base}used", "true" if token.used else "false"),
        (f"{base}cell_domain", token.cell_domain),
        (f"{base}node_number", str(token.node_number)),
        (f"{base}assigned_domain", token.assigned_domain),
    ]


def keys_to_record(token: str, data: dict[str, str]) -> JoinTokenRecord:
    base = _base(token)
    return JoinTokenRecord(
        token=token,
        created_at=data.get(f"{base}created_at"),
        expires_at=data.get(f"{base}expires_at"),
        used=data.get(f"{base}used"),
        cell_domain=data.get(f"{base}cell_domain"),
        node_number=data.get(f"{base}node_number"),
        assigned_domain=data.get(f"{base}assigned_domain"),
    )


def record_to_domain(record: JoinTokenRecord) -> Result[JoinToken, DomainError]:
    if record.created_at is None:
        return Err(NotFound("JoinToken", record.token))
    if record.expires_at is None or record.used is None:
        return Err(ValidationError("JoinToken", f"неполные данные для token={record.token}"))
    if record.cell_domain is None or record.node_number is None or record.assigned_domain is None:
        return Err(ValidationError("JoinToken", f"токен устарел (нет cell_domain/node_number): token={record.token}"))
    try:
        created_at = datetime.fromisoformat(record.created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        expires_at = datetime.fromisoformat(record.expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        used = record.used == "true"
        node_number = int(record.node_number)
    except ValueError as e:
        return Err(ValidationError("JoinToken", str(e)))
    return Ok(JoinToken(
        token=record.token,
        created_at=created_at,
        expires_at=expires_at,
        used=used,
        cell_domain=record.cell_domain,
        node_number=node_number,
        assigned_domain=record.assigned_domain,
    ))


def prefix_to_domain(token: str, data: dict[str, str]) -> Result[JoinToken, DomainError]:
    record = keys_to_record(token, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
