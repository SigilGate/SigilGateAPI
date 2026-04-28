import json
from datetime import datetime, timezone

from sigilgateapp.domain.entities import Appeal, AppealId, Message, PubId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import DomainError, NotFound, ValidationError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.records.appeal_record import AppealRecord

_NS = "/public/appeals/"


def _base(appeal_id: str) -> str:
    return f"{_NS}{appeal_id}/"


def _messages_to_json(messages: tuple[Message, ...]) -> str:
    return json.dumps([
        {"from_pub_id": m.from_pub_id, "text": m.text, "ts": m.ts.isoformat()}
        for m in messages
    ], ensure_ascii=False)


def _json_to_messages(raw: str) -> tuple[Message, ...]:
    items = json.loads(raw)
    result = []
    for item in items:
        ts = datetime.fromisoformat(item["ts"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        result.append(Message(
            from_pub_id=PubId(int(item["from_pub_id"])),
            text=item["text"],
            ts=ts,
        ))
    return tuple(result)


def domain_to_keys(appeal: Appeal) -> list[tuple[str, str]]:
    base = _base(appeal.appeal_id)
    keys: list[tuple[str, str]] = [
        (f"{base}pub_id", str(appeal.pub_id)),
        (f"{base}subject", appeal.subject),
        (f"{base}status", appeal.status.value),
        (f"{base}status_at", appeal.status_at.isoformat()),
        (f"{base}created", appeal.created.isoformat()),
        (f"{base}messages", _messages_to_json(appeal.messages)),
    ]
    if appeal.admin_pub_id is not None:
        keys.append((f"{base}admin_pub_id", str(appeal.admin_pub_id)))
    return keys


def keys_to_record(appeal_id: str, data: dict[str, str]) -> AppealRecord:
    base = _base(appeal_id)
    return AppealRecord(
        appeal_id=appeal_id,
        pub_id=data.get(f"{base}pub_id"),
        subject=data.get(f"{base}subject"),
        status=data.get(f"{base}status"),
        status_at=data.get(f"{base}status_at"),
        created=data.get(f"{base}created"),
        admin_pub_id=data.get(f"{base}admin_pub_id"),
        messages=data.get(f"{base}messages"),
    )


def record_to_domain(record: AppealRecord) -> Result[Appeal, DomainError]:
    if record.pub_id is None:
        return Err(NotFound("Appeal", record.appeal_id))
    if record.subject is None or record.status is None or record.status_at is None or record.created is None:
        return Err(ValidationError("Appeal", f"неполные данные для id={record.appeal_id}"))
    try:
        status = Status(record.status)
        status_at = datetime.fromisoformat(record.status_at)
        if status_at.tzinfo is None:
            status_at = status_at.replace(tzinfo=timezone.utc)
        created = datetime.fromisoformat(record.created)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        messages = _json_to_messages(record.messages) if record.messages else ()
        admin_pub_id = PubId(int(record.admin_pub_id)) if record.admin_pub_id else None
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return Err(ValidationError("Appeal", str(e)))
    return Ok(Appeal(
        appeal_id=AppealId(record.appeal_id),
        pub_id=PubId(int(record.pub_id)),
        subject=record.subject,
        status=status,
        status_at=status_at,
        created=created,
        messages=messages,
        admin_pub_id=admin_pub_id,
    ))


def prefix_to_domain(appeal_id: str, data: dict[str, str]) -> Result[Appeal, DomainError]:
    record = keys_to_record(appeal_id, data)
    return record_to_domain(record)


def namespace() -> str:
    return _NS
