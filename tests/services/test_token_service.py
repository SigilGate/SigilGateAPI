from datetime import datetime, timedelta, timezone

from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.adapters.system_ports import SystemClock, SystemRandom
from sigilgateapp.domain.errors import NotFound, TokenConsumed, TokenExpired
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import token_service

_CELL = "necodate.website"


class _FixedClock:
    def __init__(self, dt: datetime) -> None:
        self._dt = dt

    def now(self) -> datetime:
        return self._dt


def test_generate_returns_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    result = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(result, Ok)
    jt = result.value
    assert jt.token
    assert not jt.used
    assert jt.expires_at > jt.created_at


def test_generate_assigns_cell_and_domain():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    result = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(result, Ok)
    jt = result.value
    assert jt.cell_domain == _CELL
    assert jt.node_number == 1
    assert jt.assigned_domain == f"1.core.{_CELL}"


def test_generate_increments_node_number():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    r1 = token_service.generate(_CELL, etcd, clock, SystemRandom())
    r2 = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(r1, Ok)
    assert isinstance(r2, Ok)
    assert r1.value.node_number == 1
    assert r2.value.node_number == 2
    assert r1.value.assigned_domain == f"1.core.{_CELL}"
    assert r2.value.assigned_domain == f"2.core.{_CELL}"


def test_generate_token_ttl_is_24h():
    etcd = InMemoryEtcd()
    now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    clock = _FixedClock(now)
    result = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(result, Ok)
    delta = result.value.expires_at - result.value.created_at
    assert delta == timedelta(hours=24)


def test_get_existing_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    result = token_service.get(gen.value.token, etcd)
    assert isinstance(result, Ok)
    assert result.value.token == gen.value.token
    assert result.value.cell_domain == _CELL


def test_get_missing_token_returns_not_found():
    etcd = InMemoryEtcd()
    result = token_service.get("nonexistent-uuid", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_validate_valid_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    result = token_service.validate(gen.value.token, etcd, clock)
    assert isinstance(result, Ok)


def test_validate_expired_token():
    etcd = InMemoryEtcd()
    now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    gen_clock = _FixedClock(now)
    gen = token_service.generate(_CELL, etcd, gen_clock, SystemRandom())
    assert isinstance(gen, Ok)

    future_clock = _FixedClock(now + timedelta(hours=25))
    result = token_service.validate(gen.value.token, etcd, future_clock)
    assert isinstance(result, Err)
    assert isinstance(result.error, TokenExpired)


def test_validate_consumed_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    token_service.consume(gen.value.token, etcd, clock)
    result = token_service.validate(gen.value.token, etcd, clock)
    assert isinstance(result, Err)
    assert isinstance(result.error, TokenConsumed)


def test_consume_valid_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    result = token_service.consume(gen.value.token, etcd, clock)
    assert isinstance(result, Ok)
    assert result.value.used is True


def test_consume_already_consumed_returns_error():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    token_service.consume(gen.value.token, etcd, clock)
    result = token_service.consume(gen.value.token, etcd, clock)
    assert isinstance(result, Err)
    assert isinstance(result.error, TokenConsumed)


def test_revoke_token():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    gen = token_service.generate(_CELL, etcd, clock, SystemRandom())
    assert isinstance(gen, Ok)
    token_str = gen.value.token
    result = token_service.revoke(token_str, etcd)
    assert isinstance(result, Ok)
    get_result = token_service.get(token_str, etcd)
    assert isinstance(get_result, Err)
    assert isinstance(get_result.error, NotFound)


def test_revoke_missing_token_returns_not_found():
    etcd = InMemoryEtcd()
    result = token_service.revoke("nonexistent-uuid", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
