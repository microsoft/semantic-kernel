# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from typing import Any

import httpcore
import httpx


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, pinned_hosts: Mapping[str, str]):
        self._pinned_hosts = {host.lower(): address for host, address in pinned_hosts.items()}
        self._backend = httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        return await self._backend.connect_tcp(
            self._pinned_hosts.get(host.lower(), host), port, timeout, local_address, socket_options
        )


class PinnedDnsTransport(httpx.AsyncBaseTransport):
    """HTTP transport that connects validated hostnames to fixed IP addresses."""

    def __init__(self, pinned_hosts: Mapping[str, str], **kwargs: Any):
        """Initialize a transport using fixed addresses for validated hosts."""
        ssl_context = httpx.create_ssl_context(
            verify=kwargs.pop("verify", True), cert=kwargs.pop("cert", None), trust_env=kwargs.pop("trust_env", True)
        )
        limits = kwargs.pop("limits", httpx.Limits())
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected transport options: {unexpected}")
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl_context,
            max_connections=limits.max_connections,
            max_keepalive_connections=limits.max_keepalive_connections,
            keepalive_expiry=limits.keepalive_expiry,
            http1=kwargs.pop("http1", True),
            http2=kwargs.pop("http2", False),
            network_backend=_PinnedNetworkBackend(pinned_hosts),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Send a request through the pinned connection pool."""
        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        response = await self._pool.handle_async_request(req)
        return httpx.Response(
            status_code=response.status,
            headers=response.headers,
            stream=_HttpcoreResponseStream(response.stream),
            extensions=response.extensions,
            request=request,
        )

    async def aclose(self) -> None:
        """Close all pooled connections."""
        await self._pool.aclose()


class _HttpcoreResponseStream(httpx.AsyncByteStream):
    def __init__(self, stream: Any):
        self._stream = stream

    async def __aiter__(self):
        async for chunk in self._stream:
            yield chunk

    async def aclose(self) -> None:
        await self._stream.aclose()
