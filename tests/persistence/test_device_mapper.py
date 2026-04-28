from datetime import datetime, timezone

from sigilgateapp.domain.entities import Device, DeviceUuid, NodeIp, UserId
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Ok
from sigilgateapp.persistence.mappers import device_mapper

_NOW = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)


def _make_device(**kwargs) -> Device:
    defaults = dict(
        uuid=DeviceUuid("uuid-abc"), user_id=UserId(1), name="iPhone",
        status=Status.ACTIVE, status_at=_NOW, created=_NOW,
    )
    return Device(**{**defaults, **kwargs})


def test_round_trip_minimal():
    device = _make_device()
    keys = dict(device_mapper.domain_to_keys(device))
    result = device_mapper.prefix_to_domain(1, "uuid-abc", keys)
    assert result == Ok(device)


def test_round_trip_with_core_node():
    device = _make_device(core_node=NodeIp("1.2.3.4"))
    keys = dict(device_mapper.domain_to_keys(device))
    result = device_mapper.prefix_to_domain(1, "uuid-abc", keys)
    assert result == Ok(device)


def test_name_stored_under_device_key():
    device = _make_device()
    keys = dict(device_mapper.domain_to_keys(device))
    assert "/sigilgate/users/1/devices/uuid-abc/device" in keys
    assert keys["/sigilgate/users/1/devices/uuid-abc/device"] == "iPhone"


def test_core_node_absent_when_none():
    device = _make_device()
    keys = dict(device_mapper.domain_to_keys(device))
    assert "/sigilgate/users/1/devices/uuid-abc/core_node" not in keys


def test_not_found_when_device_missing():
    from sigilgateapp.domain.errors import NotFound
    from sigilgateapp.domain.result import Err
    result = device_mapper.prefix_to_domain(1, "uuid-abc", {})
    assert isinstance(result, Err)
    assert isinstance(result.error, NotFound)
