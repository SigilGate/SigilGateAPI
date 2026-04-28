from pydantic import BaseModel


class BackupLoadRequest(BaseModel):
    snapshot: dict[str, str]
