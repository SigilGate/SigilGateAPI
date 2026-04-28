from pydantic import BaseModel


class SetRouteRequest(BaseModel):
    core_ip: str
