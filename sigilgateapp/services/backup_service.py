from sigilgateapp.domain.errors import EtcdError, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.ports.etcd_port import EtcdPort

_NAMESPACES = ("/sigilgate/", "/public/")
_BATCH_SIZE = 128


def dump(etcd: EtcdPort) -> Result[dict[str, str], ServiceError]:
    try:
        data: dict[str, str] = {}
        for prefix in _NAMESPACES:
            data.update(etcd.prefix_scan(prefix))
        return Ok(data)
    except Exception as e:
        return Err(EtcdError(str(e)))


def load(snapshot: dict[str, str], etcd: EtcdPort) -> Result[int, ServiceError]:
    items = list(snapshot.items())
    try:
        for i in range(0, len(items), _BATCH_SIZE):
            batch = items[i : i + _BATCH_SIZE]
            etcd.txn([(k, v) for k, v in batch])
        return Ok(len(items))
    except Exception as e:
        return Err(EtcdError(str(e)))
