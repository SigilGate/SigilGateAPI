from fastapi import Depends, Header

from sigilgateapp.domain.entities import ApiToken
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import api_token_service
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import AppError


async def require_auth(
    authorization: str | None = Header(default=None),
    ctx: AppContext = Depends(get_ctx),
) -> ApiToken:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(401, "unauthorized", "Bearer token required")
    plaintext = authorization.removeprefix("Bearer ")
    match api_token_service.validate(plaintext, ctx.etcd, ctx.clock):
        case Ok(token):
            return token
        case Err(_):
            raise AppError(401, "unauthorized", "Недействительный токен")
