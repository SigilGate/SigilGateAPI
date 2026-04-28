from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import device_service

_UUID1 = "device-uuid-0000-0000-000000000001"
_UUID2 = "device-uuid-0000-0000-000000000002"
_USER_ID = 42


def _seed_device(etcd: InMemoryEtcd, user_id: int, uuid: str, name: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/devices/{uuid}/"
    etcd.txn([
        (f"{base}device", name),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def test_list_by_user_returns_devices():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID1, "mobile")
    _seed_device(etcd, _USER_ID, _UUID2, "laptop")
    result = device_service.list_by_user(_USER_ID, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 2
    uuids = {d.uuid for d in result.value}
    assert _UUID1 in uuids
    assert _UUID2 in uuids


def test_list_by_user_empty():
    etcd = InMemoryEtcd()
    result = device_service.list_by_user(_USER_ID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []


def test_list_by_user_does_not_return_other_users_devices():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID1, "mobile")
    _seed_device(etcd, 99, _UUID2, "other")
    result = device_service.list_by_user(_USER_ID, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 1
    assert result.value[0].uuid == _UUID1


def test_get_device_by_uuid():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID1, "mobile")
    result = device_service.get(_UUID1, etcd)
    assert isinstance(result, Ok)
    assert result.value.uuid == _UUID1
    assert result.value.user_id == _USER_ID
    assert result.value.name == "mobile"


def test_get_missing_device_returns_not_found():
    etcd = InMemoryEtcd()
    result = device_service.get("nonexistent-uuid", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_get_device_returns_correct_user_id():
    etcd = InMemoryEtcd()
    _seed_device(etcd, 77, _UUID1, "tablet")
    result = device_service.get(_UUID1, etcd)
    assert isinstance(result, Ok)
    assert result.value.user_id == 77
