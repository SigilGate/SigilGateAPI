from tests.api.conftest import AUTH_HEADERS

_UUID1 = "device-uuid-0000-0000-000000000001"
_UUID2 = "device-uuid-0000-0000-000000000002"
_USER_ID = 42


def _seed_device(etcd, user_id: int, uuid: str, name: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/devices/{uuid}/"
    etcd.txn([
        (f"{base}device", name),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def test_list_user_devices_returns_200(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID1, "mobile")
    _seed_device(test_etcd, _USER_ID, _UUID2, "laptop")
    response = client.get(f"/api/v1/users/{_USER_ID}/devices", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    uuids = {d["uuid"] for d in data}
    assert _UUID1 in uuids
    assert _UUID2 in uuids


def test_list_user_devices_empty_returns_200(client):
    response = client.get(f"/api/v1/users/{_USER_ID}/devices", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_get_device_returns_200(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID1, "mobile")
    response = client.get(f"/api/v1/devices/{_UUID1}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == _UUID1
    assert data["user_id"] == _USER_ID
    assert data["name"] == "mobile"
    assert data["status"] == "active"


def test_get_missing_device_returns_404(client):
    response = client.get("/api/v1/devices/nonexistent-uuid", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_devices_unauthenticated_returns_401(client):
    response = client.get(f"/api/v1/users/{_USER_ID}/devices")
    assert response.status_code == 401
