from fastapi import APIRouter, Depends

from sigilgateapp.api.composition import AppContext, get_ctx

router = APIRouter()


@router.get("/health")
async def health(ctx: AppContext = Depends(get_ctx)):
    etcd_status = "ok"
    try:
        ctx.etcd.get("/__health_check__")
    except Exception:
        etcd_status = "degraded"
    return {"status": "ok", "etcd": etcd_status}


@router.get("/api/v1/version")
async def version():
    return {"version": "0.1.0"}
