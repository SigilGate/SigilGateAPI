from tests.api.conftest import AUTH_HEADERS


def _seed_user(etcd, user_id: int, username: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/"
    etcd.txn([
        (f"{base}username", username),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def test_get_user_returns_200(client, test_etcd):
    _seed_user(test_etcd, 42, "alice")
    response = client.get("/api/v1/users/42", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert response.json()["status"] == "active"


def test_get_missing_user_returns_404(client):
    response = client.get("/api/v1/users/9999", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_users_unauthenticated_returns_401(client):
    response = client.get("/api/v1/users/1")
    assert response.status_code == 401
