from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import user_service


def _seed_user(etcd: InMemoryEtcd, user_id: int, username: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/"
    etcd.txn([
        (f"{base}username", username),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def test_get_existing_user():
    etcd = InMemoryEtcd()
    _seed_user(etcd, 42, "alice")
    result = user_service.get(42, etcd)
    assert isinstance(result, Ok)
    assert result.value.id == 42
    assert result.value.username == "alice"
    assert result.value.status == Status.ACTIVE


def test_get_missing_user_returns_not_found():
    etcd = InMemoryEtcd()
    result = user_service.get(999, etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_get_inactive_user():
    etcd = InMemoryEtcd()
    _seed_user(etcd, 7, "bob", "inactive")
    result = user_service.get(7, etcd)
    assert isinstance(result, Ok)
    assert result.value.status == Status.INACTIVE
