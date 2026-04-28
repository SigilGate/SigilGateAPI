from fastapi import APIRouter, Depends

from sigilgateapp.domain.entities import ApiToken
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import backup_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error
from sigilgateapp.api.schemas.backup_schemas import BackupLoadRequest

router = APIRouter()


@router.post("/backup/dump")
async def backup_dump(
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match backup_service.dump(ctx.etcd):
        case Ok(data):
            return {
                "keys_count": len(data),
                "namespaces": ["/sigilgate/", "/public/"],
                "snapshot": data,
            }
        case Err(e):
            raise http_error(e) from None


@router.post("/backup/load")
async def backup_load(
    body: BackupLoadRequest,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match backup_service.load(body.snapshot, ctx.etcd):
        case Ok(count):
            return {"loaded_keys": count}
        case Err(e):
            raise http_error(e) from None
