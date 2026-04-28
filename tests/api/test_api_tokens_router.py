from tests.api.conftest import AUTH_HEADERS


def test_list_tokens_returns_test_token(client):
    response = client.get("/api/v1/api-tokens", headers=AUTH_HEADERS)
    assert response.status_code == 200
    tokens = response.json()
    assert isinstance(tokens, list)
    assert any(t["name"] == "test" for t in tokens)


def test_create_token_returns_plaintext(client):
    response = client.post(
        "/api/v1/api-tokens",
        json={"name": "new-bot"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert "token_id" in data
    assert "token" in data
    assert data["token"].startswith("sgat_")
    assert data["name"] == "new-bot"


def test_created_token_appears_in_list(client):
    client.post("/api/v1/api-tokens", json={"name": "bot-x"}, headers=AUTH_HEADERS)
    response = client.get("/api/v1/api-tokens", headers=AUTH_HEADERS)
    names = [t["name"] for t in response.json()]
    assert "bot-x" in names


def test_revoke_token_returns_204(client):
    create_resp = client.post(
        "/api/v1/api-tokens",
        json={"name": "to-revoke"},
        headers=AUTH_HEADERS,
    )
    token_id = create_resp.json()["token_id"]

    revoke_resp = client.delete(f"/api/v1/api-tokens/{token_id}", headers=AUTH_HEADERS)
    assert revoke_resp.status_code == 204


def test_revoke_nonexistent_returns_404(client):
    response = client.delete("/api/v1/api-tokens/nonexistent-id", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_list_tokens_unauthenticated_returns_401(client):
    response = client.get("/api/v1/api-tokens")
    assert response.status_code == 401
