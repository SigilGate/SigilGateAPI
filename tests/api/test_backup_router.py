from tests.api.conftest import AUTH_HEADERS


def test_dump_returns_structure(client):
    response = client.post("/api/v1/backup/dump", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "keys_count" in data
    assert "snapshot" in data
    assert "namespaces" in data
    assert isinstance(data["snapshot"], dict)
    assert data["keys_count"] == len(data["snapshot"])


def test_load_and_dump_roundtrip(client):
    snapshot = {
        "/sigilgate/test/key1": "value1",
        "/sigilgate/test/key2": "value2",
        "/public/test/key3": "value3",
    }
    load_resp = client.post(
        "/api/v1/backup/load",
        json={"snapshot": snapshot},
        headers=AUTH_HEADERS,
    )
    assert load_resp.status_code == 200
    assert load_resp.json()["loaded_keys"] == 3

    dump_resp = client.post("/api/v1/backup/dump", headers=AUTH_HEADERS)
    assert dump_resp.status_code == 200
    dumped = dump_resp.json()["snapshot"]
    for k, v in snapshot.items():
        assert dumped.get(k) == v


def test_load_empty_snapshot(client):
    response = client.post(
        "/api/v1/backup/load",
        json={"snapshot": {}},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["loaded_keys"] == 0


def test_dump_unauthenticated_returns_401(client):
    response = client.post("/api/v1/backup/dump")
    assert response.status_code == 401


def test_load_unauthenticated_returns_401(client):
    response = client.post("/api/v1/backup/load", json={"snapshot": {}})
    assert response.status_code == 401
