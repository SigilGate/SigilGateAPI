from contextlib import asynccontextmanager

from fastapi import FastAPI

from sigilgateapp.api.composition import build_context
from sigilgateapp.api.errors import AppError, app_error_handler
from sigilgateapp.api.routers import api_tokens, backup, cells, devices, health, join_tokens, nodes, routes, subscription, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ctx = build_context()
    except Exception:
        ctx = None  # env vars отсутствуют (тесты или неправильная конфигурация)
    app.state.ctx = ctx
    yield


app = FastAPI(lifespan=lifespan, title="SigilGateApp", version="0.1.0")
app.add_exception_handler(AppError, app_error_handler)
app.include_router(health.router)
app.include_router(backup.router, prefix="/api/v1")
app.include_router(api_tokens.router, prefix="/api/v1")
app.include_router(nodes.router, prefix="/api/v1")
app.include_router(join_tokens.router, prefix="/api/v1")
app.include_router(cells.router, prefix="/api/v1")
app.include_router(routes.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(subscription.router, prefix="/api/v1")
