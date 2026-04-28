from sigilgateapp.adapters.system_ports import SystemClock
from sigilgateapp.services import route_service
from tests.api.conftest import AUTH_HEADERS

_UUID = "aaaaaaaa-1111-1111-1111-000000000001"
_CORE_IP = "10.0.0.1"


def test_list_routes_returns_200(client):
    response = client.get("/api/v1/routes", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_set_route_returns_200(client):
    response = client.put(
        f"/api/v1/routes/{_UUID}",
        json={"core_ip": _CORE_IP},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["uuid"] == _UUID
    assert response.json()["core_ip"] == _CORE_IP
    assert response.json()["status"] == "active"


def test_set_route_upsert(client, test_etcd):
    route_service.set_route(_UUID, "1.1.1.1", test_etcd, SystemClock())
    response = client.put(
        f"/api/v1/routes/{_UUID}",
        json={"core_ip": "2.2.2.2"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["core_ip"] == "2.2.2.2"


def test_get_route_returns_200(client, test_etcd):
    route_service.set_route(_UUID, _CORE_IP, test_etcd, SystemClock())
    response = client.get(f"/api/v1/routes/{_UUID}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["uuid"] == _UUID


def test_get_missing_route_returns_404(client):
    response = client.get("/api/v1/routes/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_routes_unauthenticated_returns_401(client):
    response = client.get("/api/v1/routes")
    assert response.status_code == 401
