from dataclasses import dataclass


@dataclass(frozen=True)
class PublicUserRecord:
    pub_id: str
    username: str | None = None
    hash_telegram_id: str | None = None
    telegram: str | None = None
    email: str | None = None
