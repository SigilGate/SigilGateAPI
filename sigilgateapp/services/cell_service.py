from sigilgateapp.domain.entities import Node
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.errors import EtcdError, NotFound, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.services import node_service
from sigilgateapp.ports.etcd_port import EtcdPort


def _is_cell(node: Node) -> bool:
    return node.role == NodeRole.ENTRY and node.domain is not None


def get(ip: str, etcd: EtcdPort) -> Result[Node, ServiceError]:
    match node_service.get(ip, etcd):
        case Err(e):
            return Err(e)
        case Ok(node) if _is_cell(node):
            return Ok(node)
        case Ok(_):
            return Err(NotFound("Cell", ip))


def list_cells(
    status_filter: Status | None,
    etcd: EtcdPort,
) -> Result[list[Node], ServiceError]:
    match node_service.list_nodes(NodeRole.ENTRY, status_filter, etcd):
        case Err(e):
            return Err(e)
        case Ok(nodes):
            return Ok([n for n in nodes if n.domain is not None])
