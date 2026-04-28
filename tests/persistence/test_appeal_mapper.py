from datetime import datetime, timezone

from sigilgateapp.domain.entities import Appeal, AppealId, Message, PubId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Ok
from sigilgateapp.persistence.mappers import appeal_mapper

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def _make_appeal(**kwargs) -> Appeal:
    defaults = dict(
        appeal_id=AppealId("appeal-uuid"),
        pub_id=PubId(42),
        subject="Проблема с подключением",
        status=Status.ACTIVE,
        status_at=_NOW,
        created=_NOW,
    )
    return Appeal(**{**defaults, **kwargs})


def test_round_trip_minimal():
    appeal = _make_appeal()
    keys = dict(appeal_mapper.domain_to_keys(appeal))
    result = appeal_mapper.prefix_to_domain("appeal-uuid", keys)
    assert result == Ok(appeal)


def test_round_trip_with_messages_and_admin():
    msg = Message(from_pub_id=PubId(1), text="Привет", ts=_NOW)
    appeal = _make_appeal(
        messages=(msg,),
        admin_pub_id=PubId(99),
    )
    keys = dict(appeal_mapper.domain_to_keys(appeal))
    result = appeal_mapper.prefix_to_domain("appeal-uuid", keys)
    assert result == Ok(appeal)


def test_messages_stored_as_json_blob():
    import json
    msg = Message(from_pub_id=PubId(1), text="test", ts=_NOW)
    appeal = _make_appeal(messages=(msg,))
    keys = dict(appeal_mapper.domain_to_keys(appeal))
    blob = keys["/public/appeals/appeal-uuid/messages"]
    parsed = json.loads(blob)
    assert len(parsed) == 1
    assert parsed[0]["text"] == "test"


def test_admin_pub_id_absent_when_none():
    appeal = _make_appeal()
    keys = dict(appeal_mapper.domain_to_keys(appeal))
    assert "/public/appeals/appeal-uuid/admin_pub_id" not in keys


def test_not_found_when_pub_id_missing():
    from sigilgateapp.domain.errors import NotFound
    from sigilgateapp.domain.result import Err
    result = appeal_mapper.prefix_to_domain("appeal-uuid", {})
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
