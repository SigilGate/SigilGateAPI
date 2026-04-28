from datetime import datetime, timezone

from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.adapters.system_ports import SystemClock
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.errors import AlreadyExists, NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.persistence.mappers import node_mapper
from sigilgateapp.services import node_service


def _seed_node(etcd: InMemoryEtcd, ip: str, role: str, status: str, domain: str | None = None) -> None:
    now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    data = [(f"/sigilgate/nodes/{ip}/role", role),
            (f"/sigilgate/nodes/{ip}/status", status),
            (f"/sigilgate/nodes/{ip}/status_at", now.isoformat())]
    if domain:
        data.append((f"/sigilgate/nodes/{ip}/domain", domain))
    etcd.txn(data)


def test_register_new_node_creates_active():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    result = node_service.register("1.2.3.4", NodeRole.CORE, "1.core.necodate.website", None, None, "api.svc", "necodate.website", 1, etcd, clock)
    assert isinstance(result, Ok)
    node = result.value
    assert node.ip == "1.2.3.4"
    assert node.role == NodeRole.CORE
    assert node.status == Status.ACTIVE
    assert node.domain == "1.core.necodate.website"
    assert node.cell_domain == "necodate.website"
    assert node.node_number == 1
    assert node.core_service_name == "api.svc"


def test_register_existing_node_returns_already_exists():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    _seed_node(etcd, "1.2.3.4", "core", "inactive", "old.example.com")
    result = node_service.register("1.2.3.4", NodeRole.CORE, "new.example.com", None, None, "api.svc.new", None, None, etcd, clock)
    assert isinstance(result, Err)
    assert isinstance(result.error, AlreadyExists)


def test_get_existing_node():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.1", "entry", "active", "entry.example.com")
    result = node_service.get("10.0.0.1", etcd)
    assert isinstance(result, Ok)
    assert result.value.ip == "10.0.0.1"
    assert result.value.role == NodeRole.ENTRY


def test_get_missing_node_returns_not_found():
    etcd = InMemoryEtcd()
    result = node_service.get("9.9.9.9", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_list_nodes_no_filter():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "1.0.0.1", "core", "active")
    _seed_node(etcd, "1.0.0.2", "entry", "active")
    _seed_node(etcd, "1.0.0.3", "mgmt", "inactive")
    result = node_service.list_nodes(None, None, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 3


def test_list_nodes_filter_by_role():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "1.0.0.1", "core", "active")
    _seed_node(etcd, "1.0.0.2", "entry", "active")
    result = node_service.list_nodes(NodeRole.CORE, None, etcd)
    assert isinstance(result, Ok)
    ips = [n.ip for n in result.value]
    assert "1.0.0.1" in ips
    assert "1.0.0.2" not in ips


def test_list_nodes_filter_by_status():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "1.0.0.1", "core", "active")
    _seed_node(etcd, "1.0.0.2", "core", "inactive")
    result = node_service.list_nodes(None, Status.INACTIVE, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 1
    assert result.value[0].ip == "1.0.0.2"


def test_set_status_updates_node():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    _seed_node(etcd, "2.2.2.2", "core", "active")
    result = node_service.set_status("2.2.2.2", Status.INACTIVE, etcd, clock)
    assert isinstance(result, Ok)
    assert result.value.status == Status.INACTIVE


def test_set_status_missing_node_returns_not_found():
    etcd = InMemoryEtcd()
    clock = SystemClock()
    result = node_service.set_status("9.9.9.9", Status.INACTIVE, etcd, clock)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
