from fastapi import Request
from fastapi.responses import JSONResponse

from sigilgateapp.domain.errors import (
    AlreadyExists,
    EtcdError,
    Forbidden,
    NotFound,
    ServiceError,
    TokenConsumed,
    TokenExpired,
    ValidationError,
)


class AppError(Exception):
    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )


def http_error(error: ServiceError) -> AppError:
    match error:
        case NotFound(entity=entity, key=key):
            return AppError(404, "not_found", f"{entity} не найден: {key}")
        case AlreadyExists(entity=entity, key=key):
            return AppError(409, "already_exists", f"{entity} уже существует: {key}")
        case ValidationError(field=field, message=message):
            return AppError(422, "validation_error", f"{field}: {message}")
        case Forbidden(message=message):
            return AppError(403, "forbidden", message)
        case TokenExpired(token=token):
            return AppError(404, "token_expired", f"Токен истёк: {token}")
        case TokenConsumed(token=token):
            return AppError(409, "token_consumed", f"Токен уже использован: {token}")
        case EtcdError(message=message):
            return AppError(503, "storage_unavailable", message)
        case _:
            return AppError(500, "internal_error", str(error))
