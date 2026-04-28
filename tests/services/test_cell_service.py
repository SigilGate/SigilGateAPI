from datetime import datetime, timezone

from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import cell_service


def _seed_node(etcd: InMemoryEtcd, ip: str, role: str, status: str,
               domain: str | None = None, client_service_name: str | None = None) -> None:
    now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    data = [
        (f"/sigilgate/nodes/{ip}/role", role),
        (f"/sigilgate/nodes/{ip}/status", status),
        (f"/sigilgate/nodes/{ip}/status_at", now.isoformat()),
    ]
    if domain:
        data.append((f"/sigilgate/nodes/{ip}/domain", domain))
    if client_service_name:
        data.append((f"/sigilgate/nodes/{ip}/client_service_name", client_service_name))
    etcd.txn(data)


def test_get_cell_returns_entry_node_with_domain():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.1", "entry", "active", "entry.example.com")
    result = cell_service.get("10.0.0.1", etcd)
    assert isinstance(result, Ok)
    assert result.value.domain == "entry.example.com"


def test_get_core_node_returns_not_found():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.2", "core", "active", "core.example.com")
    result = cell_service.get("10.0.0.2", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_get_entry_without_domain_returns_not_found():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.3", "entry", "active")
    result = cell_service.get("10.0.0.3", etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_list_cells_returns_only_entry_with_domain():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.1", "entry", "active", "entry.example.com")
    _seed_node(etcd, "10.0.0.2", "core", "active", "core.example.com")
    _seed_node(etcd, "10.0.0.3", "entry", "active")
    result = cell_service.list_cells(None, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 1
    assert result.value[0].ip == "10.0.0.1"


def test_list_cells_filter_by_status():
    etcd = InMemoryEtcd()
    _seed_node(etcd, "10.0.0.1", "entry", "active", "e1.example.com")
    _seed_node(etcd, "10.0.0.2", "entry", "inactive", "e2.example.com")
    result = cell_service.list_cells(Status.ACTIVE, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 1
    assert result.value[0].ip == "10.0.0.1"
