from datetime import timedelta

from sigilgateapp.domain.entities import JoinToken
from sigilgateapp.domain.errors import EtcdError, NotFound, ServiceError, TokenConsumed, TokenExpired
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence import id_allocator
from sigilgateapp.persistence.mappers import join_token_mapper
from sigilgateapp.ports.clock_port import ClockPort
from sigilgateapp.ports.etcd_port import EtcdPort
from sigilgateapp.ports.random_port import RandomPort

_TTL_HOURS = 24


def _counter_key(cell_domain: str) -> str:
    return f"/sigilgate/cells/{cell_domain}/core_node_counter"


def generate(
    cell_domain: str,
    etcd: EtcdPort,
    clock: ClockPort,
    random: RandomPort,
) -> Result[JoinToken, ServiceError]:
    match id_allocator.allocate_id(_counter_key(cell_domain), etcd):
        case Err(e):
            return Err(e)
        case Ok(node_number):
            pass
    now = clock.now()
    token = JoinToken(
        token=random.uuid(),
        created_at=now,
        expires_at=now + timedelta(hours=_TTL_HOURS),
        used=False,
        cell_domain=cell_domain,
        node_number=node_number,
        assigned_domain=f"{node_number}.core.{cell_domain}",
    )
    try:
        etcd.txn(join_token_mapper.domain_to_keys(token))
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok(token)


def get(token: str, etcd: EtcdPort) -> Result[JoinToken, ServiceError]:
    ns = join_token_mapper.namespace()
    try:
        data = etcd.prefix_scan(f"{ns}{token}/")
    except Exception as e:
        return Err(EtcdError(str(e)))
    return join_token_mapper.prefix_to_domain(token, data)


def validate(token: str, etcd: EtcdPort, clock: ClockPort) -> Result[JoinToken, ServiceError]:
    match get(token, etcd):
        case Err(e):
            return Err(e)
        case Ok(jt):
            if jt.used:
                return Err(TokenConsumed(token))
            if jt.expires_at < clock.now():
                return Err(TokenExpired(token))
            return Ok(jt)


def consume(token: str, etcd: EtcdPort, clock: ClockPort) -> Result[JoinToken, ServiceError]:
    match validate(token, etcd, clock):
        case Err(e):
            return Err(e)
        case Ok(jt):
            try:
                etcd.put(f"{join_token_mapper.namespace()}{token}/used", "true")
            except Exception as e:
                return Err(EtcdError(str(e)))
            from dataclasses import replace
            return Ok(replace(jt, used=True))


def revoke(token: str, etcd: EtcdPort) -> Result[None, ServiceError]:
    ns = join_token_mapper.namespace()
    try:
        data = etcd.prefix_scan(f"{ns}{token}/")
        if not data:
            return Err(NotFound("JoinToken", token))
        etcd.txn([(k, None) for k in data])
    except Exception as e:
        return Err(EtcdError(str(e)))
    return Ok(None)
