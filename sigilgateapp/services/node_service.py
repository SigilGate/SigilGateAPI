from sigilgateapp.domain.entities import CellDomain, Node, NodeIp
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.errors import AlreadyExists, EtcdError, NotFound, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.mappers import node_mapper
from sigilgateapp.ports.clock_port import ClockPort
from sigilgateapp.ports.etcd_port import EtcdPort


def _extract_ips(data: dict[str, str]) -> set[str]:
    ns = node_mapper.namespace()
    ips: set[str] = set()
    for key in data:
        rest = key[len(ns):]
        slash = rest.find("/")
        if slash > 0:
            ips.add(rest[:slash])
    return ips


def register(
    ip: str,
    role: NodeRole,
    domain: str | None,
    uuid: str | None,
    client_service_name: str | None,
    core_service_name: str | None,
    cell_domain: str | None,
    node_number: int | None,
    etcd: EtcdPort,
    clock: ClockPort,
) -> Result[Node, ServiceError]:
    ns = node_mapper.namespace()
    try:
        existing_data = etcd.prefix_scan(f"{ns}{ip}/")
    except Exception as e:
        return Err(EtcdError(str(e)))

    match node_mapper.prefix_to_domain(ip, existing_data):
        case Ok(_):
            return Err(AlreadyExists("Node", ip))
        case _:
            node = Node(
                ip=NodeIp(ip),
                role=role,
                status=Status.ACTIVE,
                status_at=clock.now(),
                domain=domain,
                cell_domain=CellDomain(cell_domain) if cell_domain is not None else None,
                node_number=node_number,
                uuid=uuid,
                client_service_name=client_service_name,
                core_service_name=core_service_name,
            )

    try:
        etcd.txn(node_mapper.domain_to_keys(node))
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok(node)


def get(ip: str, etcd: EtcdPort) -> Result[Node, ServiceError]:
    ns = node_mapper.namespace()
    try:
        data = etcd.prefix_scan(f"{ns}{ip}/")
    except Exception as e:
        return Err(EtcdError(str(e)))
    return node_mapper.prefix_to_domain(ip, data)


def list_nodes(
    role_filter: NodeRole | None,
    status_filter: Status | None,
    etcd: EtcdPort,
) -> Result[list[Node], ServiceError]:
    ns = node_mapper.namespace()
    try:
        data = etcd.prefix_scan(ns)
    except Exception as e:
        return Err(EtcdError(str(e)))
    nodes: list[Node] = []
    for ip in sorted(_extract_ips(data)):
        prefix = f"{ns}{ip}/"
        node_data = {k: v for k, v in data.items() if k.startswith(prefix)}
        match node_mapper.prefix_to_domain(ip, node_data):
            case Ok(node):
                if role_filter is not None and node.role != role_filter:
                    continue
                if status_filter is not None and node.status != status_filter:
                    continue
                nodes.append(node)
    return Ok(nodes)


def set_status(
    ip: str,
    status: Status,
    etcd: EtcdPort,
    clock: ClockPort,
) -> Result[Node, ServiceError]:
    match get(ip, etcd):
        case Err(e):
            return Err(e)
        case Ok(node):
            updated = Node(
                ip=node.ip,
                role=node.role,
                status=status,
                status_at=clock.now(),
                domain=node.domain,
                cell_domain=node.cell_domain,
                node_number=node.node_number,
                uuid=node.uuid,
                client_service_name=node.client_service_name,
                core_service_name=node.core_service_name,
            )
            try:
                etcd.txn([
                    (f"{node_mapper.namespace()}{ip}/status", status.value),
                    (f"{node_mapper.namespace()}{ip}/status_at", updated.status_at.isoformat()),
                ])
            except Exception as e:
                return Err(EtcdError(str(e)))
            return Ok(updated)
