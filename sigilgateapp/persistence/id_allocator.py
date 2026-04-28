from sigilgateapp.domain.errors import EtcdError, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.ports.etcd_port import EtcdPort

MAX_RETRIES = 10


def allocate_id(counter_key: str, etcd: EtcdPort) -> Result[int, ServiceError]:
    for _ in range(MAX_RETRIES):
        current = etcd.get(counter_key)
        next_id = int(current) + 1 if current is not None else 1
        if etcd.compare_and_swap(counter_key, current, str(next_id)):
            return Ok(next_id)
    return Err(EtcdError(f"не удалось выделить ID по ключу {counter_key}"))
