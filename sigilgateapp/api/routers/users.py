from fastapi import APIRouter, Depends

from sigilgateapp.domain.entities import ApiToken, User
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import user_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error

router = APIRouter()


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "status": user.status.value,
        "status_at": user.status_at.isoformat(),
        "created": user.created.isoformat(),
        "hash_telegram_id": user.hash_telegram_id,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match user_service.get(user_id, ctx.etcd):
        case Ok(user):
            return _user_dict(user)
        case Err(e):
            raise http_error(e) from None
