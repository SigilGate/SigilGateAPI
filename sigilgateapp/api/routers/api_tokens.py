from fastapi import APIRouter, Depends

from sigilgateapp.domain.entities import ApiToken
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import api_token_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error
from sigilgateapp.api.schemas.api_token_schemas import CreateApiTokenRequest

router = APIRouter()


@router.get("/api-tokens")
async def list_tokens(
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match api_token_service.list_all(ctx.etcd):
        case Ok(tokens):
            return [
                {
                    "token_id": t.token_id,
                    "name": t.name,
                    "created": t.created.isoformat(),
                    "active": t.active,
                    "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
                }
                for t in tokens
            ]
        case Err(e):
            raise http_error(e) from None


@router.post("/api-tokens", status_code=201)
async def create_token(
    body: CreateApiTokenRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match api_token_service.create(body.name, ctx.etcd, ctx.random, ctx.clock):
        case Ok((token, plaintext)):
            return {
                "token_id": token.token_id,
                "name": token.name,
                "token": plaintext,
            }
        case Err(e):
            raise http_error(e) from None


@router.delete("/api-tokens/{token_id}", status_code=204)
async def revoke_token(
    token_id: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match api_token_service.revoke(token_id, ctx.etcd):
        case Ok(_):
            return None
        case Err(e):
            raise http_error(e) from None
