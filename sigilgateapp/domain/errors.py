from dataclasses import dataclass


@dataclass(frozen=True)
class NotFound:
    entity: str
    key: str


@dataclass(frozen=True)
class AlreadyExists:
    entity: str
    key: str


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


@dataclass(frozen=True)
class Forbidden:
    message: str


@dataclass(frozen=True)
class EtcdError:
    message: str


@dataclass(frozen=True)
class TokenExpired:
    token: str


@dataclass(frozen=True)
class TokenConsumed:
    token: str


type DomainError = NotFound | AlreadyExists | ValidationError | Forbidden | TokenExpired | TokenConsumed
type ServiceError = DomainError | EtcdError
