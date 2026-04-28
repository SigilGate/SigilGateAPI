from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.domain.errors import EtcdError
from sigilgateapp.domain.result import Err, Ok
from sigilgateapp.persistence.id_allocator import MAX_RETRIES, allocate_id

_KEY = "/sigilgate/counters/test_id"


def test_first_allocation_returns_1():
    etcd = InMemoryEtcd()
    result = allocate_id(_KEY, etcd)
    assert result == Ok(1)


def test_sequential_allocations_are_monotonic():
    etcd = InMemoryEtcd()
    ids = [allocate_id(_KEY, etcd) for _ in range(5)]
    assert ids == [Ok(1), Ok(2), Ok(3), Ok(4), Ok(5)]


def test_counter_persists_in_etcd():
    etcd = InMemoryEtcd()
    allocate_id(_KEY, etcd)
    allocate_id(_KEY, etcd)
    assert etcd.get(_KEY) == "2"


def test_returns_err_after_max_retries_exhausted():
    class AlwaysFailCas:
        def get(self, key: str) -> str | None:
            return None

        def compare_and_swap(self, key: str, expected: str | None, value: str) -> bool:
            return False

    result = allocate_id(_KEY, AlwaysFailCas())  # type: ignore[arg-type]
    assert isinstance(result, Err)
    assert isinstance(result.error, EtcdError)
