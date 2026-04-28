from pydantic import BaseModel

from sigilgateapp.domain.enums import Status


class SetCellStatusRequest(BaseModel):
    status: Status
