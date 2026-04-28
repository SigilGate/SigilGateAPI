from datetime import datetime, timezone

import pytest

from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd


@pytest.fixture
def etcd() -> InMemoryEtcd:
    return InMemoryEtcd()


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
