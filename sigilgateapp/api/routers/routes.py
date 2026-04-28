from fastapi import APIRouter, Depends, Query

from sigilgateapp.domain.entities import ApiToken, Route
from sigilgateapp.domain.enums import Status
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import route_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error
from sigilgateapp.api.schemas.route_schemas import SetRouteRequest

router = APIRouter()


def _route_dict(route: Route) -> dict:
    return {
        "uuid": route.uuid,
        "core_ip": route.core_ip,
        "status": route.status.value,
        "status_at": route.status_at.isoformat(),
    }


@router.get("/routes")
async def list_routes(
    status: Status | None = Query(default=None),
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match route_service.list_routes(status, ctx.etcd):
        case Ok(routes):
            return [_route_dict(r) for r in routes]
        case Err(e):
            raise http_error(e) from None


@router.get("/routes/{uuid}")
async def get_route(
    uuid: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match route_service.get(uuid, ctx.etcd):
        case Ok(route):
            return _route_dict(route)
        case Err(e):
            raise http_error(e) from None


@router.put("/routes/{uuid}")
async def set_route(
    uuid: str,
    body: SetRouteRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match route_service.set_route(uuid, body.core_ip, ctx.etcd, ctx.clock):
        case Ok(route):
            return _route_dict(route)
        case Err(e):
            raise http_error(e) from None
