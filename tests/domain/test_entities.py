from datetime import datetime, timezone

from sigilgateapp.domain.entities import (
    Device,
    DeviceUuid,
    Node,
    NodeIp,
    Route,
    User,
    UserId,
)
from sigilgateapp.domain.enums import NodeRole, Status

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def test_user_is_immutable():
    user = User(id=UserId(1), username="test", status=Status.ACTIVE, status_at=_NOW, created=_NOW)
    try:
        user.username = "other"  # type: ignore[misc]
        assert False, "должно упасть"
    except Exception:
        pass


def test_user_core_nodes_set_semantics():
    ip1, ip2 = NodeIp("1.2.3.4"), NodeIp("5.6.7.8")
    user = User(
        id=UserId(1), username="u", status=Status.ACTIVE,
        status_at=_NOW, created=_NOW,
        core_nodes=frozenset([ip1, ip2]),
    )
    assert ip1 in user.core_nodes
    assert ip2 in user.core_nodes
    assert len(user.core_nodes) == 2


def test_device_core_node_none_by_default():
    device = Device(
        uuid=DeviceUuid("uuid-1"), user_id=UserId(1), name="iPhone",
        status=Status.ACTIVE, status_at=_NOW, created=_NOW,
    )
    assert device.core_node is None


def test_node_has_no_created_field():
    node = Node(ip=NodeIp("1.2.3.4"), role=NodeRole.CORE, status=Status.ACTIVE, status_at=_NOW)
    assert not hasattr(node, "created")


def test_node_optional_fields_default_none():
    node = Node(ip=NodeIp("1.2.3.4"), role=NodeRole.MGMT, status=Status.ACTIVE, status_at=_NOW)
    assert node.domain is None
    assert node.client_service_name is None
    assert node.core_service_name is None


def test_route_fields():
    route = Route(
        uuid=DeviceUuid("uuid-1"),
        core_ip=NodeIp("1.2.3.4"),
        status=Status.ACTIVE,
        status_at=_NOW,
    )
    assert route.uuid == "uuid-1"
    assert route.core_ip == "1.2.3.4"
