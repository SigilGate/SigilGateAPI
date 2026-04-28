from sigilgateapp.domain.entities import Device
from sigilgateapp.domain.errors import EtcdError, NotFound, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.mappers import device_mapper
from sigilgateapp.ports.etcd_port import EtcdPort

_USERS_NS = "/sigilgate/users/"


def _extract_uuids(data: dict[str, str], devices_prefix: str) -> set[str]:
    uuids: set[str] = set()
    for key in data:
        rest = key[len(devices_prefix):]
        slash = rest.find("/")
        if slash > 0:
            uuids.add(rest[:slash])
    return uuids


def list_by_user(user_id: int, etcd: EtcdPort) -> Result[list[Device], ServiceError]:
    devices_prefix = device_mapper.devices_prefix(user_id)
    try:
        data = etcd.prefix_scan(devices_prefix)
    except Exception as e:
        return Err(EtcdError(str(e)))
    devices: list[Device] = []
    for uuid in sorted(_extract_uuids(data, devices_prefix)):
        prefix = f"{devices_prefix}{uuid}/"
        device_data = {k: v for k, v in data.items() if k.startswith(prefix)}
        match device_mapper.prefix_to_domain(user_id, uuid, device_data):
            case Ok(device):
                devices.append(device)
    return Ok(devices)


def get(uuid: str, etcd: EtcdPort) -> Result[Device, ServiceError]:
    # Full scan required: devices are nested under users and indexed only by user_id+uuid.
    try:
        all_data = etcd.prefix_scan(_USERS_NS)
    except Exception as e:
        return Err(EtcdError(str(e)))

    fragment = f"/devices/{uuid}/"
    for key in all_data:
        if fragment in key:
            parts = key.split("/")
            try:
                user_id = int(parts[3])
            except (IndexError, ValueError):
                continue
            prefix = f"{device_mapper.devices_prefix(user_id)}{uuid}/"
            device_data = {k: v for k, v in all_data.items() if k.startswith(prefix)}
            return device_mapper.prefix_to_domain(user_id, uuid, device_data)

    return Err(NotFound("Device", uuid))
