from pydantic import BaseModel


class GenerateTokenRequest(BaseModel):
    cell_domain: str
