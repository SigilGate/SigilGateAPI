from fastapi import APIRouter, Depends, Query

from sigilgateapp.domain.entities import ApiToken, Node
from sigilgateapp.domain.enums import NodeRole, Status
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import node_service, token_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error
from sigilgateapp.api.schemas.node_schemas import JoinNodeRequest, RegisterNodeRequest, SetNodeStatusRequest

router = APIRouter()


def _node_dict(node: Node) -> dict:
    return {
        "ip": node.ip,
        "role": node.role.value,
        "status": node.status.value,
        "status_at": node.status_at.isoformat(),
        "domain": node.domain,
        "cell_domain": node.cell_domain,
        "node_number": node.node_number,
        "uuid": node.uuid,
        "client_service_name": node.client_service_name,
        "core_service_name": node.core_service_name,
    }


@router.get("/nodes")
async def list_nodes(
    role: NodeRole | None = Query(default=None),
    status: Status | None = Query(default=None),
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match node_service.list_nodes(role, status, ctx.etcd):
        case Ok(nodes):
            return [_node_dict(n) for n in nodes]
        case Err(e):
            raise http_error(e) from None


@router.post("/nodes", status_code=201)
async def register_node(
    body: RegisterNodeRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match node_service.register(
        body.ip, body.role, body.domain,
        body.uuid, body.client_service_name, body.core_service_name,
        body.cell_domain, body.node_number,
        ctx.etcd, ctx.clock,
    ):
        case Ok(node):
            return _node_dict(node)
        case Err(e):
            raise http_error(e) from None


@router.post("/nodes/join", status_code=201)
async def join_node(body: JoinNodeRequest, ctx: AppContext = Depends(get_ctx)):
    match token_service.consume(body.join_token, ctx.etcd, ctx.clock):
        case Err(e):
            raise http_error(e) from None
        case Ok(jt):
            pass
    match node_service.register(
        body.ip, NodeRole.CORE,
        jt.assigned_domain, body.uuid, None, body.core_service_name,
        jt.cell_domain, jt.node_number,
        ctx.etcd, ctx.clock,
    ):
        case Ok(node):
            return _node_dict(node)
        case Err(e):
            raise http_error(e) from None


@router.get("/nodes/{ip}")
async def get_node(
    ip: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match node_service.get(ip, ctx.etcd):
        case Ok(node):
            return _node_dict(node)
        case Err(e):
            raise http_error(e) from None


@router.patch("/nodes/{ip}/status")
async def set_node_status(
    ip: str,
    body: SetNodeStatusRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match node_service.set_status(ip, body.status, ctx.etcd, ctx.clock):
        case Ok(node):
            return _node_dict(node)
        case Err(e):
            raise http_error(e) from None
