from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceRecord:
    uuid: str
    user_id: str
    # этcd-ключ: "device", domain-поле: "name"
    device: str | None = None
    status: str | None = None
    status_at: str | None = None
    created: str | None = None
    core_node: str | None = None
