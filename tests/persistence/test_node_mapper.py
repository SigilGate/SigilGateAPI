from datetime import datetime, timezone

from sigilgateapp.domain.entities import Node, NodeIp
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.result import Ok
from sigilgateapp.persistence.mappers import node_mapper

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def _make_node(**kwargs) -> Node:
    defaults = dict(
        ip=NodeIp("1.2.3.4"), role=NodeRole.CORE,
        status=Status.ACTIVE, status_at=_NOW,
    )
    return Node(**{**defaults, **kwargs})


def test_round_trip_core_node():
    node = _make_node(domain="1.core.necodate.website", cell_domain="necodate.website", node_number=1, core_service_name="grpc-service")
    keys = dict(node_mapper.domain_to_keys(node))
    result = node_mapper.prefix_to_domain("1.2.3.4", keys)
    assert result == Ok(node)


def test_round_trip_core_node_with_uuid():
    node = _make_node(domain="core.example.com", uuid="3f84a022-bef7-4256-8428-5c5d113b9fa6", core_service_name="grpc-service")
    keys = dict(node_mapper.domain_to_keys(node))
    result = node_mapper.prefix_to_domain("1.2.3.4", keys)
    assert result == Ok(node)


def test_round_trip_entry_node():
    node = _make_node(role=NodeRole.ENTRY, domain="entry.example.com", client_service_name="client-svc")
    keys = dict(node_mapper.domain_to_keys(node))
    result = node_mapper.prefix_to_domain("1.2.3.4", keys)
    assert result == Ok(node)


def test_round_trip_mgmt_node():
    node = _make_node(role=NodeRole.MGMT)
    keys = dict(node_mapper.domain_to_keys(node))
    result = node_mapper.prefix_to_domain("1.2.3.4", keys)
    assert result == Ok(node)


def test_optional_fields_absent_when_none():
    node = _make_node()
    keys = dict(node_mapper.domain_to_keys(node))
    assert "/sigilgate/nodes/1.2.3.4/domain" not in keys
    assert "/sigilgate/nodes/1.2.3.4/cell_domain" not in keys
    assert "/sigilgate/nodes/1.2.3.4/node_number" not in keys
    assert "/sigilgate/nodes/1.2.3.4/uuid" not in keys
    assert "/sigilgate/nodes/1.2.3.4/client_service_name" not in keys
    assert "/sigilgate/nodes/1.2.3.4/core_service_name" not in keys


def test_not_found_when_role_missing():
    from sigilgateapp.domain.errors import NotFound
    from sigilgateapp.domain.result import Err
    result = node_mapper.prefix_to_domain("1.2.3.4", {})
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
