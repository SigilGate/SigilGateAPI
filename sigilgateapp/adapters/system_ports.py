import uuid
from datetime import datetime, timezone


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SystemRandom:
    def uuid(self) -> str:
        return str(uuid.uuid4())
