from datetime import datetime, timezone

from sigilgateapp.adapters.system_ports import SystemClock, SystemRandom
from sigilgateapp.services import token_service
from tests.api.conftest import AUTH_HEADERS

_CELL = "necodate.website"


def _seed_node(etcd, ip: str, role: str, status: str, domain: str | None = None) -> None:
    now = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    data = [(f"/sigilgate/nodes/{ip}/role", role),
            (f"/sigilgate/nodes/{ip}/status", status),
            (f"/sigilgate/nodes/{ip}/status_at", now.isoformat())]
    if domain:
        data.append((f"/sigilgate/nodes/{ip}/domain", domain))
    etcd.txn(data)


def _make_join_token(etcd) -> str:
    result = token_service.generate(_CELL, etcd, SystemClock(), SystemRandom())
    return result.value.token


def test_list_nodes_returns_200(client):
    response = client.get("/api/v1/nodes", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_register_node_returns_201(client):
    response = client.post(
        "/api/v1/nodes",
        json={"ip": "5.5.5.5", "role": "core", "domain": "test.example.com", "core_service_name": "api.svc"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ip"] == "5.5.5.5"
    assert data["role"] == "core"
    assert data["status"] == "active"
    assert data["domain"] == "test.example.com"


def test_register_existing_node_returns_409(client, test_etcd):
    _seed_node(test_etcd, "6.6.6.6", "core", "inactive", "old.example.com")
    response = client.post(
        "/api/v1/nodes",
        json={"ip": "6.6.6.6", "role": "core", "domain": "new.example.com"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 409
    assert response.json()["error"] == "already_exists"


def test_get_node_returns_200(client, test_etcd):
    _seed_node(test_etcd, "7.7.7.7", "entry", "active", "entry.example.com")
    response = client.get("/api/v1/nodes/7.7.7.7", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["ip"] == "7.7.7.7"
    assert response.json()["role"] == "entry"


def test_get_missing_node_returns_404(client):
    response = client.get("/api/v1/nodes/9.9.9.9", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_set_node_status_returns_200(client, test_etcd):
    _seed_node(test_etcd, "8.8.8.8", "core", "active")
    response = client.patch(
        "/api/v1/nodes/8.8.8.8/status",
        json={"status": "inactive"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_set_status_missing_node_returns_404(client):
    response = client.patch(
        "/api/v1/nodes/9.9.9.9/status",
        json={"status": "inactive"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_nodes_unauthenticated_returns_401(client):
    response = client.get("/api/v1/nodes")
    assert response.status_code == 401


# --- /nodes/join ---

def test_join_node_returns_201(client, test_etcd):
    token = _make_join_token(test_etcd)
    response = client.post(
        "/api/v1/nodes/join",
        json={
            "join_token": token,
            "ip": "10.0.0.1",
            "uuid": "3f84a022-bef7-4256-8428-5c5d113b9fa6",
            "core_service_name": "api.v2.rpc.abcdef01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ip"] == "10.0.0.1"
    assert data["role"] == "core"
    assert data["status"] == "active"
    assert data["cell_domain"] == _CELL
    assert data["node_number"] == 1
    assert data["domain"] == f"1.core.{_CELL}"


def test_join_node_consumes_token(client, test_etcd):
    token = _make_join_token(test_etcd)
    client.post(
        "/api/v1/nodes/join",
        json={"join_token": token, "ip": "10.0.0.2", "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "core_service_name": "svc"},
    )
    # second use of the same token must fail
    response = client.post(
        "/api/v1/nodes/join",
        json={"join_token": token, "ip": "10.0.0.3", "uuid": "aaaaaaaa-bbbb-cccc-dddd-ffffffffffff", "core_service_name": "svc"},
    )
    assert response.status_code == 409
    assert response.json()["error"] == "token_consumed"


def test_join_node_invalid_token_returns_400(client):
    response = client.post(
        "/api/v1/nodes/join",
        json={"join_token": "nonexistent-token", "ip": "10.0.0.4", "uuid": "uuid", "core_service_name": "svc"},
    )
    assert response.status_code == 404


def test_join_node_no_auth_required(client, test_etcd):
    token = _make_join_token(test_etcd)
    response = client.post(
        "/api/v1/nodes/join",
        json={"join_token": token, "ip": "10.0.0.5", "uuid": "aaaaaaaa-0000-0000-0000-000000000001", "core_service_name": "svc"},
    )
    assert response.status_code == 201
