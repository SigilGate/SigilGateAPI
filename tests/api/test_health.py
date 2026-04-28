def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["etcd"] == "ok"


def test_version_returns_semver(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"
