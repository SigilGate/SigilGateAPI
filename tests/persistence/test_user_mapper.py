from datetime import datetime, timezone

from sigilgateapp.domain.entities import NodeIp, User, UserId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Ok
from sigilgateapp.persistence.mappers import user_mapper

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def _make_user(**kwargs) -> User:
    defaults = dict(
        id=UserId(1), username="testuser", status=Status.ACTIVE,
        status_at=_NOW, created=_NOW,
    )
    return User(**{**defaults, **kwargs})


def test_round_trip_minimal():
    user = _make_user()
    keys = dict(user_mapper.domain_to_keys(user))
    data = {k: v for k, v in keys.items()}
    result = user_mapper.prefix_to_domain(1, data)
    assert result == Ok(user)


def test_round_trip_with_telegram_and_core_nodes():
    user = _make_user(
        hash_telegram_id="abc123",
        core_nodes=frozenset([NodeIp("1.2.3.4"), NodeIp("5.6.7.8")]),
    )
    keys = dict(user_mapper.domain_to_keys(user))
    result = user_mapper.prefix_to_domain(1, keys)
    assert result == Ok(user)


def test_domain_to_keys_contains_expected_paths():
    user = _make_user()
    keys = dict(user_mapper.domain_to_keys(user))
    assert "/sigilgate/users/1/username" in keys
    assert "/sigilgate/users/1/status" in keys
    assert "/sigilgate/users/1/status_at" in keys
    assert "/sigilgate/users/1/created" in keys
    assert keys["/sigilgate/users/1/username"] == "testuser"
    assert keys["/sigilgate/users/1/status"] == "active"


def test_hash_telegram_id_absent_when_none():
    user = _make_user(hash_telegram_id=None)
    keys = dict(user_mapper.domain_to_keys(user))
    assert "/sigilgate/users/1/hash_telegram_id" not in keys


def test_core_nodes_stored_as_subkeys():
    user = _make_user(core_nodes=frozenset([NodeIp("10.0.0.1")]))
    keys = dict(user_mapper.domain_to_keys(user))
    assert "/sigilgate/users/1/core_nodes/10.0.0.1" in keys
    assert keys["/sigilgate/users/1/core_nodes/10.0.0.1"] == ""


def test_not_found_when_username_missing():
    from sigilgateapp.domain.errors import NotFound
    from sigilgateapp.domain.result import Err
    result = user_mapper.prefix_to_domain(99, {})
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
