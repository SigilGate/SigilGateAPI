from datetime import datetime, timezone

from tests.api.conftest import AUTH_HEADERS


def _seed_node(etcd, ip: str, role: str, status: str,
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


def test_list_cells_returns_200(client, test_etcd):
    _seed_node(test_etcd, "10.0.0.1", "entry", "active", "entry.example.com")
    response = client.get("/api/v1/cells", headers=AUTH_HEADERS)
    assert response.status_code == 200
    cells = response.json()
    assert any(c["ip"] == "10.0.0.1" for c in cells)


def test_list_cells_excludes_core_nodes(client, test_etcd):
    _seed_node(test_etcd, "10.0.0.1", "entry", "active", "entry.example.com")
    _seed_node(test_etcd, "10.0.0.2", "core", "active", "core.example.com")
    response = client.get("/api/v1/cells", headers=AUTH_HEADERS)
    ips = [c["ip"] for c in response.json()]
    assert "10.0.0.2" not in ips


def test_get_cell_returns_200(client, test_etcd):
    _seed_node(test_etcd, "10.0.0.1", "entry", "active", "entry.example.com", "api.v2.rpc.abc123")
    response = client.get("/api/v1/cells/10.0.0.1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "entry.example.com"
    assert body["client_service_name"] == "api.v2.rpc.abc123"


def test_get_core_as_cell_returns_404(client, test_etcd):
    _seed_node(test_etcd, "10.0.0.2", "core", "active", "core.example.com")
    response = client.get("/api/v1/cells/10.0.0.2", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_cells_unauthenticated_returns_401(client):
    response = client.get("/api/v1/cells")
    assert response.status_code == 401
