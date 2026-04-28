from tests.api.conftest import AUTH_HEADERS

_USER_ID = 42
_UUID = "device-uuid-0000-0000-000000000001"
_CORE_IP = "10.0.0.1"
_ENTRY_IP = "10.0.0.10"
_DOMAIN = "entry.example.com"
_CLIENT_SERVICE = "api.v2.rpc.b1ed7e16ac482765"


def _seed_device(etcd, user_id: int, uuid: str, status: str = "active") -> None:
    base = f"/sigilgate/users/{user_id}/devices/{uuid}/"
    etcd.txn([
        (f"{base}device", "mobile"),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}created", "2026-02-01T00:00:00+00:00"),
    ])


def _seed_entry_node(etcd, ip: str, domain: str, service_name: str, status: str = "active") -> None:
    base = f"/sigilgate/nodes/{ip}/"
    etcd.txn([
        (f"{base}role", "entry"),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
        (f"{base}domain", domain),
        (f"{base}client_service_name", service_name),
    ])


def _seed_route(etcd, uuid: str, core_ip: str, status: str = "active") -> None:
    base = f"/sigilgate/routes/{uuid}/"
    etcd.txn([
        (f"{base}core_ip", core_ip),
        (f"{base}status", status),
        (f"{base}status_at", "2026-04-19T12:00:00+00:00"),
    ])


def test_subscription_returns_200_with_vless_url(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID)
    _seed_entry_node(test_etcd, _ENTRY_IP, _DOMAIN, _CLIENT_SERVICE)
    _seed_route(test_etcd, _UUID, _CORE_IP)
    response = client.get(f"/api/v1/subscription/{_UUID}")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert f"vless://{_UUID}@{_DOMAIN}:443" in body
    assert f"serviceName={_CLIENT_SERVICE}" in body
    assert "type=grpc" in body


def test_subscription_missing_device_returns_404(client):
    response = client.get(f"/api/v1/subscription/{_UUID}")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_subscription_device_without_route_returns_empty(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID)
    _seed_entry_node(test_etcd, _ENTRY_IP, _DOMAIN, _CLIENT_SERVICE)
    response = client.get(f"/api/v1/subscription/{_UUID}")
    assert response.status_code == 200
    assert response.text == ""


def test_subscription_is_public_no_auth_required(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID)
    response = client.get(f"/api/v1/subscription/{_UUID}")
    assert response.status_code == 200


def test_subscription_integration_entry_node_and_route(client, test_etcd):
    _seed_device(test_etcd, _USER_ID, _UUID)

    node_response = client.post("/api/v1/nodes", headers=AUTH_HEADERS, json={
        "ip": _ENTRY_IP,
        "role": "entry",
        "domain": _DOMAIN,
        "client_service_name": _CLIENT_SERVICE,
    })
    assert node_response.status_code == 201

    route_response = client.put(f"/api/v1/routes/{_UUID}", headers=AUTH_HEADERS, json={
        "core_ip": _CORE_IP,
    })
    assert route_response.status_code == 200

    sub_response = client.get(f"/api/v1/subscription/{_UUID}")
    assert sub_response.status_code == 200
    body = sub_response.text
    assert f"vless://{_UUID}@{_DOMAIN}:443" in body
    assert f"serviceName={_CLIENT_SERVICE}" in body
    assert "type=grpc" in body
