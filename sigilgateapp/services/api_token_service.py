import hashlib
from dataclasses import replace

from sigilgateapp.domain.entities import ApiToken, TokenId
from sigilgateapp.domain.errors import EtcdError, NotFound, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.mappers import api_token_mapper
from sigilgateapp.ports.clock_port import ClockPort
from sigilgateapp.ports.etcd_port import EtcdPort
from sigilgateapp.ports.random_port import RandomPort


def _hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def _extract_token_ids(data: dict[str, str]) -> set[str]:
    ns = api_token_mapper.namespace()
    ids: set[str] = set()
    for key in data:
        rest = key[len(ns):]
        slash = rest.find("/")
        if slash > 0:
            ids.add(rest[:slash])
    return ids


def create(
    name: str,
    etcd: EtcdPort,
    random: RandomPort,
    clock: ClockPort,
) -> Result[tuple[ApiToken, str], ServiceError]:
    token_id = TokenId(random.uuid())
    plaintext = "sgat_" + random.uuid().replace("-", "")
    token = ApiToken(
        token_id=token_id,
        name=name,
        token_hash=_hash(plaintext),
        created=clock.now(),
        active=True,
    )
    try:
        etcd.txn(api_token_mapper.domain_to_keys(token))
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok((token, plaintext))


def validate(plaintext: str, etcd: EtcdPort, clock: ClockPort) -> Result[ApiToken, ServiceError]:
    token_hash = _hash(plaintext)
    try:
        data = etcd.prefix_scan(api_token_mapper.namespace())
    except Exception as e:
        return Err(EtcdError(str(e)))
    ns = api_token_mapper.namespace()
    for token_id in _extract_token_ids(data):
        prefix = f"{ns}{token_id}/"
        token_data = {k: v for k, v in data.items() if k.startswith(prefix)}
        match api_token_mapper.prefix_to_domain(token_id, token_data):
            case Ok(token) if token.token_hash == token_hash and token.active:
                now = clock.now()
                try:
                    etcd.put(f"{prefix}last_used_at", now.isoformat())
                except Exception:
                    pass
                return Ok(replace(token, last_used_at=now))
            case _:
                continue
    return Err(NotFound("ApiToken", "by_hash"))


def list_all(etcd: EtcdPort) -> Result[list[ApiToken], ServiceError]:
    try:
        data = etcd.prefix_scan(api_token_mapper.namespace())
    except Exception as e:
        return Err(EtcdError(str(e)))
    ns = api_token_mapper.namespace()
    tokens: list[ApiToken] = []
    for token_id in sorted(_extract_token_ids(data)):
        prefix = f"{ns}{token_id}/"
        token_data = {k: v for k, v in data.items() if k.startswith(prefix)}
        match api_token_mapper.prefix_to_domain(token_id, token_data):
            case Ok(token):
                tokens.append(token)
            case _:
                pass
    return Ok(tokens)


def revoke(token_id: str, etcd: EtcdPort) -> Result[None, ServiceError]:
    ns = api_token_mapper.namespace()
    prefix = f"{ns}{token_id}/"
    try:
        data = etcd.prefix_scan(prefix)
        if not data:
            return Err(NotFound("ApiToken", token_id))
        etcd.put(f"{prefix}active", "false")
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok(None)
