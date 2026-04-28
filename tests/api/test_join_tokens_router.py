from sigilgateapp.adapters.system_ports import SystemClock, SystemRandom
from sigilgateapp.services import token_service
from tests.api.conftest import AUTH_HEADERS

_CELL = "necodate.website"
_GENERATE_BODY = {"cell_domain": _CELL}


def _generate_token(etcd) -> str:
    result = token_service.generate(_CELL, etcd, SystemClock(), SystemRandom())
    return result.value.token


def test_generate_token_returns_201(client):
    response = client.post("/api/v1/tokens/join", json=_GENERATE_BODY, headers=AUTH_HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert "expires_at" in data
    assert data["cell_domain"] == _CELL
    assert data["node_number"] == 1
    assert data["assigned_domain"] == f"1.core.{_CELL}"


def test_generate_token_increments_node_number(client):
    r1 = client.post("/api/v1/tokens/join", json=_GENERATE_BODY, headers=AUTH_HEADERS)
    r2 = client.post("/api/v1/tokens/join", json=_GENERATE_BODY, headers=AUTH_HEADERS)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["node_number"] == 1
    assert r2.json()["node_number"] == 2


def test_generate_token_requires_cell_domain(client):
    response = client.post("/api/v1/tokens/join", json={}, headers=AUTH_HEADERS)
    assert response.status_code == 422


def test_get_token_returns_200(client, test_etcd):
    token = _generate_token(test_etcd)
    response = client.get(f"/api/v1/tokens/join/{token}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["token"] == token
    assert response.json()["used"] is False
    assert response.json()["cell_domain"] == _CELL


def test_get_missing_token_returns_404(client):
    response = client.get("/api/v1/tokens/join/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_consume_token_returns_200(client, test_etcd):
    token = _generate_token(test_etcd)
    response = client.post(f"/api/v1/tokens/join/{token}/consume", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["used"] is True


def test_consume_already_consumed_returns_409(client, test_etcd):
    token = _generate_token(test_etcd)
    client.post(f"/api/v1/tokens/join/{token}/consume", headers=AUTH_HEADERS)
    response = client.post(f"/api/v1/tokens/join/{token}/consume", headers=AUTH_HEADERS)
    assert response.status_code == 409
    assert response.json()["error"] == "token_consumed"


def test_revoke_token_returns_204(client, test_etcd):
    token = _generate_token(test_etcd)
    response = client.delete(f"/api/v1/tokens/join/{token}", headers=AUTH_HEADERS)
    assert response.status_code == 204


def test_revoke_missing_token_returns_404(client):
    response = client.delete("/api/v1/tokens/join/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_tokens_unauthenticated_returns_401(client):
    response = client.post("/api/v1/tokens/join", json=_GENERATE_BODY)
    assert response.status_code == 401
