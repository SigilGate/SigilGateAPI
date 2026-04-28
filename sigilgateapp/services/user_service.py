from sigilgateapp.domain.entities import User
from sigilgateapp.domain.errors import EtcdError, ServiceError
from sigilgateapp.domain.result import Err, Ok, Result
from sigilgateapp.persistence.mappers import user_mapper
from sigilgateapp.ports.etcd_port import EtcdPort


def get(user_id: int, etcd: EtcdPort) -> Result[User, ServiceError]:
    ns = user_mapper.namespace()
    try:
        data = etcd.prefix_scan(f"{ns}{user_id}/")
    except Exception as e:
        return Err(EtcdError(str(e)))
    return user_mapper.prefix_to_domain(user_id, data)
