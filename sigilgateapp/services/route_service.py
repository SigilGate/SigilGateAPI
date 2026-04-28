from sigilgateapp.domain.entities import DeviceUuid, NodeIp, Route
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.errors import EtcdError, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.mappers import route_mapper
from sigilgateapp.ports.clock_port import ClockPort
from sigilgateapp.ports.etcd_port import EtcdPort


def _extract_uuids(data: dict[str, str]) -> set[str]:
    ns = route_mapper.namespace()
    uuids: set[str] = set()
    for key in data:
        rest = key[len(ns):]
        slash = rest.find("/")
        if slash > 0:
            uuids.add(rest[:slash])
    return uuids


def set_route(
    uuid: str,
    core_ip: str,
    etcd: EtcdPort,
    clock: ClockPort,
) -> Result[Route, ServiceError]:
    route = Route(
        uuid=DeviceUuid(uuid),
        core_ip=NodeIp(core_ip),
        status=Status.ACTIVE,
        status_at=clock.now(),
    )
    try:
        etcd.txn(route_mapper.domain_to_keys(route))
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok(route)


def get(uuid: str, etcd: EtcdPort) -> Result[Route, ServiceError]:
    ns = route_mapper.namespace()
    try:
        data = etcd.prefix_scan(f"{ns}{uuid}/")
    except Exception as e:
        return Err(EtcdError(str(e)))
    return route_mapper.prefix_to_domain(uuid, data)


def list_routes(
    status_filter: Status | None,
    etcd: EtcdPort,
) -> Result[list[Route], ServiceError]:
    ns = route_mapper.namespace()
    try:
        data = etcd.prefix_scan(ns)
    except Exception as e:
        return Err(EtcdError(str(e)))
    routes: list[Route] = []
    for uuid in sorted(_extract_uuids(data)):
        prefix = f"{ns}{uuid}/"
        route_data = {k: v for k, v in data.items() if k.startswith(prefix)}
        match route_mapper.prefix_to_domain(uuid, route_data):
            case Ok(route):
                if status_filter is None or route.status == status_filter:
                    routes.append(route)
    return Ok(routes)
