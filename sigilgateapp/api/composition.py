import os
from dataclasses import dataclass

from fastapi import Request

from sigilgateapp.adapters.etcd_adapter import EtcdAdapter
from sigilgateapp.adapters.system_ports import SystemClock, SystemRandom


@dataclass
class AppContext:
    etcd: EtcdAdapter
    clock: SystemClock
    random: SystemRandom


def build_context() -> AppContext:
    endpoints = os.environ["SIGILGATEAPP_ETCD_ENDPOINTS"].split(",")
    ca_cert = os.environ["SIGILGATEAPP_ETCD_CA_CERT"]
    cert = os.environ["SIGILGATEAPP_ETCD_CLIENT_CERT"]
    key = os.environ["SIGILGATEAPP_ETCD_CLIENT_KEY"]
    return AppContext(
        etcd=EtcdAdapter(endpoints=endpoints, ca_cert=ca_cert, cert=cert, key=key),
        clock=SystemClock(),
        random=SystemRandom(),
    )


def get_ctx(request: Request) -> AppContext:
    ctx: AppContext | None = request.app.state.ctx
    if ctx is None:
        raise RuntimeError("AppContext не инициализирован. Проверьте env vars.")
    return ctx
