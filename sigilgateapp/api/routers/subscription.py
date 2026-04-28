from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.services import subscription_service
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.api.errors import http_error

router = APIRouter()


@router.get("/subscription/{device_uuid}", response_class=PlainTextResponse)
async def get_subscription(
    device_uuid: str,
    ctx: AppContext = Depends(get_ctx),
):
    match subscription_service.get_subscription(device_uuid, ctx.etcd):
        case Ok(urls):
            return "\n".join(urls)
        case Err(e):
            raise http_error(e) from None
