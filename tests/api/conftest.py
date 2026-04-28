import hashlib
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from sigilgateapp.adapters.inmemory_etcd import InMemoryEtcd
from sigilgateapp.adapters.system_ports import SystemClock, SystemRandom
from sigilgateapp.api.app import app
from sigilgateapp.api.composition import AppContext, get_ctx
from sigilgateapp.domain.entities import ApiToken, TokenId
from sigilgateapp.persistence.mappers import api_token_mapper

TEST_TOKEN_PLAINTEXT = "sgat_testtoken123"
TEST_TOKEN_HASH = hashlib.sha256(TEST_TOKEN_PLAINTEXT.encode()).hexdigest()
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN_PLAINTEXT}"}


@pytest.fixture
def test_etcd() -> InMemoryEtcd:
    etcd = InMemoryEtcd()
    token = ApiToken(
        token_id=TokenId("test-token-id"),
        name="test",
        token_hash=TEST_TOKEN_HASH,
        created=datetime(2026, 4, 19, tzinfo=timezone.utc),
        active=True,
    )
    for key, value in api_token_mapper.domain_to_keys(token):
        etcd.put(key, value)
    return etcd


@pytest.fixture
def client(test_etcd: InMemoryEtcd):
    ctx = AppContext(etcd=test_etcd, clock=SystemClock(), random=SystemRandom())
    app.dependency_overrides[get_ctx] = lambda: ctx
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
