from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.result import Ok
from sigilgateapp.services import backup_service


def test_dump_empty():
    etcd = InMemoryEtcd()
    result = backup_service.dump(etcd)
    assert isinstance(result, Ok)
    assert result.value == {}


def test_load_and_dump_roundtrip():
    etcd = InMemoryEtcd()
    snapshot = {
        "/sigilgate/users/1/username": "alice",
        "/sigilgate/users/1/status": "active",
        "/public/contacts/1/email": "alice@example.com",
    }
    load_result = backup_service.load(snapshot, etcd)
    assert isinstance(load_result, Ok)
    assert load_result.value == 3

    dump_result = backup_service.dump(etcd)
    assert isinstance(dump_result, Ok)
    assert dump_result.value == snapshot


def test_load_empty_snapshot():
    etcd = InMemoryEtcd()
    result = backup_service.load({}, etcd)
    assert isinstance(result, Ok)
    assert result.value == 0


def test_load_large_snapshot_batching():
    etcd = InMemoryEtcd()
    snapshot = {f"/sigilgate/test/key{i}": f"value{i}" for i in range(300)}
    result = backup_service.load(snapshot, etcd)
    assert isinstance(result, Ok)
    assert result.value == 300
    dump = backup_service.dump(etcd)
    assert isinstance(dump, Ok)
    assert dump.value == snapshot


def test_dump_skips_unrelated_namespaces():
    etcd = InMemoryEtcd()
    etcd.put("/other/key", "value")
    etcd.put("/sigilgate/key", "sg_value")
    result = backup_service.dump(etcd)
    assert isinstance(result, Ok)
    assert "/other/key" not in result.value
    assert "/sigilgate/key" in result.value
