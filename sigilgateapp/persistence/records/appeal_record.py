from dataclasses import dataclass


@dataclass(frozen=True)
class AppealRecord:
    appeal_id: str
    pub_id: str | None = None
    subject: str | None = None
    status: str | None = None
    status_at: str | None = None
    created: str | None = None
    admin_pub_id: str | None = None
    messages: str | None = None  # JSON blob
