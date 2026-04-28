from sigilgateapp.persistence.mappers import api_token_mapper
from tests.api.conftest import AUTH_HEADERS, TEST_TOKEN_PLAINTEXT


def test_missing_auth_header_returns_401(client):
    response = client.post("/api/v1/backup/dump")
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"


def test_wrong_scheme_returns_401(client):
    response = client.post(
        "/api/v1/backup/dump",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 401


def test_invalid_token_returns_401(client):
    response = client.post(
        "/api/v1/backup/dump",
        headers={"Authorization": "Bearer sgat_invalid_token"},
    )
    assert response.status_code == 401


def test_valid_token_accepted(client):
    response = client.post("/api/v1/backup/dump", headers=AUTH_HEADERS)
    assert response.status_code == 200


def test_valid_token_updates_last_used_at(client, test_etcd):
    ns = api_token_mapper.namespace()
    key = f"{ns}test-token-id/last_used_at"
    assert test_etcd.get(key) is None
    client.post("/api/v1/backup/dump", headers=AUTH_HEADERS)
    assert test_etcd.get(key) is not None
