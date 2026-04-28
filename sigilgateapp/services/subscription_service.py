from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.ports.etcd_port import EtcdPort
from sigilgateapp.services import cell_service, device_service, route_service


def _vless_url(device_uuid: str, domain: str, service_name: str) -> str:
    return (
        f"vless://{device_uuid}@{domain}:443"
        f"?encryption=none&security=tls&sni={domain}&type=grpc&serviceName={service_name}"
    )


def get_subscription(device_uuid: str, etcd: EtcdPort) -> Result[list[str], ServiceError]:
    match device_service.get(device_uuid, etcd):
        case Err(e):
            return Err(e)
        case Ok(device) if device.status != Status.ACTIVE:
            return Ok([])
        case Ok(_):
            pass

    match route_service.get(device_uuid, etcd):
        case Err(_):
            return Ok([])
        case Ok(route) if route.status != Status.ACTIVE:
            return Ok([])
        case Ok(_):
            pass

    match cell_service.list_cells(Status.ACTIVE, etcd):
        case Err(e):
            return Err(e)
        case Ok(cells):
            pass

    urls = [
        _vless_url(device_uuid, cell.domain, cell.client_service_name)
        for cell in cells
        if cell.domain and cell.client_service_name
    ]
    return Ok(urls)
