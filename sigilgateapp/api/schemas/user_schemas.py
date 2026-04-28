from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    hash_telegram_id: str | None = None
