from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.errors import NotFound
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import subscription_service

_USER_ID = 42
_UUID = "device-uuid-0000-0000-000000000001"
_CORE_IP = "10.0.0.1"
_ENTRY_IP = "10.0.0.10"
_DOMAIN = "entry.example.com"
_CLIENT_SERVICE = "api.v2.rpc.b1ed7e16ac482765"


def _seed_device(etcd: InMemoryEtcd, user_id: int, uuid: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/devices/{uuid}/"
    etcd.txn([
        (f"{base}device", "mobile"),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def _seed_entry_node(etcd: InMemoryEtcd, ip: str, status: str = "active",
                     domain: str | None = None, client_service_name: str | None = None) -> None:
    base = f"/sigilgate/nodes/{ip}/"
    keys = [
        (f"{base}role", "entry"),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
    ]
    if domain:
        keys.append((f"{base}domain", domain))
    if client_service_name:
        keys.append((f"{base}client_service_name", client_service_name))
    etcd.txn(keys)


def _seed_route(etcd: InMemoryEtcd, uuid: str, core_ip: str, status: str = "active") -> None:
    base = f"/sigilgate/routes/{uuid}/"
    etcd.txn([
        (f"{base}core_ip", core_ip),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
    ])


def test_get_subscription_returns_vless_url():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, _ENTRY_IP, domain=_DOMAIN, client_service_name=_CLIENT_SERVICE)
    _seed_route(etcd, _UUID, _CORE_IP)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 1
    url = result.value[0]
    assert url.startswith(f"vless://{_UUID}@{_DOMAIN}:443")
    assert f"serviceName={_CLIENT_SERVICE}" in url
    assert "type=grpc" in url


def test_get_subscription_returns_one_url_per_entry_cell():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, "10.0.0.10", domain="e1.example.com", client_service_name="svc-1")
    _seed_entry_node(etcd, "10.0.0.11", domain="e2.example.com", client_service_name="svc-2")
    _seed_route(etcd, _UUID, _CORE_IP)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert len(result.value) == 2
    domains = {url.split("@")[1].split(":")[0] for url in result.value}
    assert domains == {"e1.example.com", "e2.example.com"}


def test_get_subscription_missing_device_returns_not_found():
    etcd = InMemoryEtcd()
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)


def test_get_subscription_inactive_device_returns_empty():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID, status="inactive")
    _seed_entry_node(etcd, _ENTRY_IP, domain=_DOMAIN, client_service_name=_CLIENT_SERVICE)
    _seed_route(etcd, _UUID, _CORE_IP)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []


def test_get_subscription_no_route_returns_empty():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, _ENTRY_IP, domain=_DOMAIN, client_service_name=_CLIENT_SERVICE)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []


def test_get_subscription_inactive_route_returns_empty():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, _ENTRY_IP, domain=_DOMAIN, client_service_name=_CLIENT_SERVICE)
    _seed_route(etcd, _UUID, _CORE_IP, status="inactive")
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []


def test_get_subscription_no_active_entry_cells_returns_empty():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, _ENTRY_IP, status="inactive", domain=_DOMAIN, client_service_name=_CLIENT_SERVICE)
    _seed_route(etcd, _UUID, _CORE_IP)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []


def test_get_subscription_skips_cell_without_client_service_name():
    etcd = InMemoryEtcd()
    _seed_device(etcd, _USER_ID, _UUID)
    _seed_entry_node(etcd, _ENTRY_IP, domain=_DOMAIN)
    _seed_route(etcd, _UUID, _CORE_IP)
    result = subscription_service.get_subscription(_UUID, etcd)
    assert isinstance(result, Ok)
    assert result.value == []
