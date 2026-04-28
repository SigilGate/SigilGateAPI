import base64
from urllib.parse import urlparse

import etcd3gw


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


class EtcdAdapter:
    def __init__(
        self,
        endpoints: list[str],
        ca_cert: str,
        cert: str,
        key: str,
    ) -> None:
        # etcd3gw работает с одним хостом; HA обеспечивается самим etcd-кластером
        parsed = urlparse(endpoints[0])
        self._client = etcd3gw.client(
            host=parsed.hostname,
            port=parsed.port or 2379,
            ca_cert=ca_cert,
            cert_cert=cert,
            cert_key=key,
            protocol="https",
        )

    def get(self, key: str) -> str | None:
        result = self._client.get(key)
        if not result:
            return None
        value = result[0]
        return value.decode() if isinstance(value, bytes) else value

    def put(self, key: str, value: str) -> None:
        self._client.put(key, value)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def prefix_scan(self, prefix: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for value, meta in self._client.get_prefix(prefix):
            k = meta["key"]
            k = k.decode() if isinstance(k, bytes) else k
            v = value.decode() if isinstance(value, bytes) else value
            out[k] = v
        return out

    def txn(self, ops: list[tuple[str, str | None]]) -> None:
        success = []
        for key, value in ops:
            if value is None:
                success.append({"request_delete": {"key": _b64(key)}})
            else:
                success.append({"request_put": {"key": _b64(key), "value": _b64(value)}})
        self._client.transaction({"compare": [], "success": success, "failure": []})

    def compare_and_swap(self, key: str, expected: str | None, value: str) -> bool:
        if expected is None:
            # ключ не должен существовать: version == 0
            compare = [{"key": _b64(key), "result": "EQUAL", "target": "VERSION", "version": "0"}]
        else:
            compare = [{"key": _b64(key), "result": "EQUAL", "target": "VALUE", "value": _b64(expected)}]

        success = [{"request_put": {"key": _b64(key), "value": _b64(value)}}]
        result = self._client.transaction({"compare": compare, "success": success, "failure": []})
        succeeded = result.get("succeeded", False)
        return bool(succeeded)
