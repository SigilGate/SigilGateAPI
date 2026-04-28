from fastapi import APIRouter, Depends, Query

from sigilgateapp.domain.entities import ApiToken, Node
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import cell_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error

router = APIRouter()


def _cell_dict(node: Node) -> dict:
    return {
        "ip": node.ip,
        "domain": node.domain,
        "client_service_name": node.client_service_name,
        "status": node.status.value,
        "status_at": node.status_at.isoformat(),
    }


@router.get("/cells")
async def list_cells(
    status: Status | None = Query(default=None),
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match cell_service.list_cells(status, ctx.etcd):
        case Ok(cells):
            return [_cell_dict(c) for c in cells]
        case Err(e):
            raise http_error(e) from None


@router.get("/cells/{ip}")
async def get_cell(
    ip: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match cell_service.get(ip, ctx.etcd):
        case Ok(cell):
            return _cell_dict(cell)
        case Err(e):
            raise http_error(e) from None
