from fastapi import APIRouter, Depends

from sigilgateapp.domain.entities import ApiToken, JoinToken
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import token_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error
from sigilgateapp.api.schemas.join_token_schemas import GenerateTokenRequest

router = APIRouter()


def _token_dict(jt: JoinToken) -> dict:
    return {
        "token": jt.token,
        "created_at": jt.created_at.isoformat(),
        "expires_at": jt.expires_at.isoformat(),
        "used": jt.used,
        "cell_domain": jt.cell_domain,
        "node_number": jt.node_number,
        "assigned_domain": jt.assigned_domain,
    }


@router.post("/tokens/join", status_code=201)
async def generate_token(
    body: GenerateTokenRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match token_service.generate(body.cell_domain, ctx.etcd, ctx.clock, ctx.random):
        case Ok(jt):
            return {
                "token": jt.token,
                "cell_domain": jt.cell_domain,
                "node_number": jt.node_number,
                "assigned_domain": jt.assigned_domain,
                "expires_at": jt.expires_at.isoformat(),
            }
        case Err(e):
            raise http_error(e) from None


@router.get("/tokens/join/{token}")
async def get_token(
    token: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match token_service.get(token, ctx.etcd):
        case Ok(jt):
            return _token_dict(jt)
        case Err(e):
            raise http_error(e) from None


@router.post("/tokens/join/{token}/consume")
async def consume_token(
    token: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match token_service.consume(token, ctx.etcd, ctx.clock):
        case Ok(jt):
            return {"token": jt.token, "used": jt.used}
        case Err(e):
            raise http_error(e) from None


@router.delete("/tokens/join/{token}", status_code=204)
async def revoke_token(
    token: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match token_service.revoke(token, ctx.etcd):
        case Ok(_):
            return None
        case Err(e):
            raise http_error(e) from None
