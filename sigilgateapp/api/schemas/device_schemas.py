from pydantic import BaseModel


class AddDeviceRequest(BaseModel):
    name: str
