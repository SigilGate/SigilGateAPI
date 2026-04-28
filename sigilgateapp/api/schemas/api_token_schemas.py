from pydantic import BaseModel


class CreateApiTokenRequest(BaseModel):
    name: str
