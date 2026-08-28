# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock

import httpcore
import httpx

from semantic_kernel.connectors.openapi_plugin import pinned_http_transport
from semantic_kernel.connectors.openapi_plugin.pinned_http_transport import (
    PinnedDnsTransport,
    _PinnedNetworkBackend,
)


async def test_pinned_network_backend_tries_each_resolved_address():
    backend = _PinnedNetworkBackend({"api.example.com": ["192.0.2.1", "198.51.100.1"]})
    connection = object()
    backend._backend = AsyncMock()
    backend._backend.connect_tcp = AsyncMock(side_effect=[OSError("first address failed"), connection])

    result = await backend.connect_tcp("api.example.com", 443)

    assert result is connection
    assert [call.args[0] for call in backend._backend.connect_tcp.call_args_list] == [
        "192.0.2.1",
        "198.51.100.1",
    ]


async def test_pinned_transport_uses_https_proxy_from_environment(monkeypatch):
    monkeypatch.setattr(
        pinned_http_transport,
        "getproxies",
        lambda: {"https": "http://proxy.example:8080"},
    )
    monkeypatch.setattr(pinned_http_transport, "proxy_bypass_environment", lambda host, proxies: False)
    transport = PinnedDnsTransport({"api.example.com": ["93.184.216.34"]})

    pool = transport._pool_for_request(httpx.Request("GET", "https://api.example.com/"))

    assert isinstance(pool, httpcore.AsyncHTTPProxy)
    assert pool._proxy_url.host == b"proxy.example"
    assert pool._proxy_url.port == 8080
    await transport.aclose()
