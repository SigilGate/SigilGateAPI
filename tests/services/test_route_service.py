from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.adapters.system_ports import SystemClock
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import route_service

_UUID1 = "aaaaaaaa-0000-0000-0000-000000000001"
_UUID2 = "aaaaaaaa-0000-0000-0000-000000000002"
_CORE_IP = "10.0.0.1"


def test_set_route_creates_active_route():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    result = route_service.set_route(_UUID1, _CORE_IP, etcd, clock)
    assert isinstance(result, Ok)
    route = result.value
    assert route.uuid == _UUID1
    assert route.core_ip == _CORE_IP
    assert route.status == Status.ACTIVE


def test_set_route_upsert():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    route_service.set_route(_UUID1, "1.1.1.1", etcd, clock)
    result = route_service.set_route(_UUID1, "2.2.2.2", etcd, clock)
    assert isinstance(result, Ok)
    assert result.value.core_ip == "2.2.2.2"


def test_get_existing_route():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    route_service.set_route(_UUID1, _CORE_IP, etcd, clock)
    result = route_service.get(_UUID1, etcd)
    assert isinstance(result, Ok)
    assert result.value.uuid == _UUID1


def test_get_missing_route_returns_not_found():
    etcd = InMemoryEtcd()
    result = route_service.get("nonexistent-uuid", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_list_routes_no_filter():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    route_service.set_route(_UUID1, _CORE_IP, etcd, clock)
    route_service.set_route(_UUID2, _CORE_IP, etcd, clock)
    result = route_service.list_routes(None, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 2


def test_list_routes_filter_by_status():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    route_service.set_route(_UUID1, _CORE_IP, etcd, clock)
    # Manually set one route to archived
    etcd.put(f"/sigilgate/routes/{_UUID2}/core_ip", _CORE_IP)
    etcd.put(f"/sigilgate/routes/{_UUID2}/status", "archived")
    etcd.put(f"/sigilgate/routes/{_UUID2}/status_at", "2026-04-19T12:00:00+00:00")
    result = route_service.list_routes(Status.ACTIVE, etcd)
    assert isinstance(result, Ok)
    uuids = [r.uuid for r in result.value]
    assert _UUID1 in uuids
    assert _UUID2 not in uuids
