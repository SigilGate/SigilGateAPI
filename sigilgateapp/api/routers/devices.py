from fastapi import APIRouter, Depends

from sigilgateapp.domain.entities import ApiToken, Device
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import device_service
from sigilgateapp.api.auth import require_auth
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error

router = APIRouter()


def _device_dict(device: Device) -> dict:
    return {
        "uuid": device.uuid,
        "user_id": device.user_id,
        "name": device.name,
        "status": device.status.value,
        "status_at": device.status_at.isoformat(),
        "created": device.created.isoformat(),
        "core_node": device.core_node,
    }


@router.get("/users/{user_id}/devices")
async def list_user_devices(
    user_id: int,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match device_service.list_by_user(user_id, ctx.etcd):
        case Ok(devices):
            return [_device_dict(d) for d in devices]
        case Err(e):
            raise http_error(e) from None


@router.get("/devices/{uuid}")
async def get_device(
    uuid: str,
    ctx: AppContext = Depends(get_ctx),
    _: ApiToken = Depends(require_auth),
):
    match device_service.get(uuid, ctx.etcd):
        case Ok(device):
            return _device_dict(device)
        case Err(e):
            raise http_error(e) from None
