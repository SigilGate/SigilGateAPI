from datetime import datetime, timezone

from sigilgateapp.domain.entities import DeviceUuid, NodeIp, Route
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Ok
from sigilgateapp.persistence.mappers import route_mapper

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def _make_route(**kwargs) -> Route:
    defaults = dict(
        uuid=DeviceUuid("uuid-123"),
        core_ip=NodeIp("1.2.3.4"),
        status=Status.ACTIVE,
        status_at=_NOW,
    )
    return Route(**{**defaults, **kwargs})


def test_round_trip():
    route = _make_route()
    keys = dict(route_mapper.domain_to_keys(route))
    result = route_mapper.prefix_to_domain("uuid-123", keys)
    assert result == Ok(route)


def test_keys_contain_expected_paths():
    route = _make_route()
    keys = dict(route_mapper.domain_to_keys(route))
    assert "/sigilgate/routes/uuid-123/core_ip" in keys
    assert "/sigilgate/routes/uuid-123/status" in keys
    assert keys["/sigilgate/routes/uuid-123/core_ip"] == "1.2.3.4"


def test_not_found_when_core_ip_missing():
    from sigilgateapp.domain.errors import NotFound
    from sigilgateapp.domain.result import Err
    result = route_mapper.prefix_to_domain("uuid-123", {})
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
