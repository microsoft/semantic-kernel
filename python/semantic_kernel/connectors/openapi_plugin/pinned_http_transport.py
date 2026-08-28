# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping, Sequence
from typing import Any
from urllib import request as urllib_request
from urllib.request import getproxies

import httpcore
import httpx

proxy_bypass_environment = getattr(urllib_request, "proxy_bypass_environment")


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, pinned_hosts: Mapping[str, str | Sequence[str]]):
        self._pinned_hosts = {
            host.lower(): (address,) if isinstance(address, str) else tuple(address)
            for host, address in pinned_hosts.items()
        }
        self._backend = httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        addresses = self._pinned_hosts.get(host.lower(), (host,))
        last_error = None
        for address in addresses:
            try:
                return await self._backend.connect_tcp(address, port, timeout, local_address, socket_options)
            except (OSError, httpcore.NetworkError, httpcore.TimeoutException) as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        return await self._backend.connect_tcp(host, port, timeout, local_address, socket_options)


class PinnedDnsTransport(httpx.AsyncBaseTransport):
    """HTTP transport that connects validated hostnames to fixed IP addresses."""

    def __init__(self, pinned_hosts: Mapping[str, str | Sequence[str]], **kwargs: Any):
        """Initialize a transport using fixed addresses for validated hosts."""
        trust_env = kwargs.pop("trust_env", True)
        ssl_context = httpx.create_ssl_context(
            verify=kwargs.pop("verify", True), cert=kwargs.pop("cert", None), trust_env=trust_env
        )
        self._trust_env = trust_env
        limits = kwargs.pop("limits", httpx.Limits())
        http1 = kwargs.pop("http1", True)
        http2 = kwargs.pop("http2", False)
        proxy = kwargs.pop("proxy", None)
        local_address = kwargs.pop("local_address", None)
        retries = kwargs.pop("retries", 0)
        socket_options = kwargs.pop("socket_options", None)
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected transport options: {unexpected}")
        self._ssl_context = ssl_context
        self._limits = limits
        self._http1 = http1
        self._http2 = http2
        self._local_address = local_address
        self._retries = retries
        self._socket_options = socket_options
        self._pinned_hosts = pinned_hosts
        self._proxy = httpx.Proxy(proxy) if isinstance(proxy, (str, httpx.URL)) else proxy
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl_context,
            max_connections=limits.max_connections,
            max_keepalive_connections=limits.max_keepalive_connections,
            keepalive_expiry=limits.keepalive_expiry,
            http1=http1,
            http2=http2,
            local_address=local_address,
            retries=retries,
            socket_options=socket_options,
            network_backend=_PinnedNetworkBackend(pinned_hosts),
        )
        self._proxy_pools: dict[str, httpcore.AsyncHTTPProxy] = {}

    def _proxy_for_request(self, request: httpx.Request) -> httpx.Proxy | None:
        if self._proxy is not None or not self._trust_env:
            return self._proxy

        proxies = getproxies()
        if proxy_bypass_environment(request.url.host, proxies):
            return None
        proxy_url = proxies.get(request.url.scheme) or proxies.get("all")
        if not proxy_url:
            return None
        if "://" not in proxy_url:
            proxy_url = f"http://{proxy_url}"
        return httpx.Proxy(proxy_url)

    def _build_proxy_pool(self, proxy: httpx.Proxy) -> httpcore.AsyncHTTPProxy:
        if proxy.url.scheme not in ("http", "https"):
            raise ValueError(f"Proxy protocol must be either 'http' or 'https', but got {proxy.url.scheme!r}")
        return httpcore.AsyncHTTPProxy(
            proxy_url=httpcore.URL(
                scheme=proxy.url.raw_scheme,
                host=proxy.url.raw_host,
                port=proxy.url.port,
                target=proxy.url.raw_path,
            ),
            proxy_auth=proxy.raw_auth,
            proxy_headers=proxy.headers.raw,
            proxy_ssl_context=proxy.ssl_context,
            ssl_context=self._ssl_context,
            max_connections=self._limits.max_connections,
            max_keepalive_connections=self._limits.max_keepalive_connections,
            keepalive_expiry=self._limits.keepalive_expiry,
            http1=self._http1,
            http2=self._http2,
            local_address=self._local_address,
            retries=self._retries,
            socket_options=self._socket_options,
            network_backend=_PinnedNetworkBackend({}),
        )

    def _pool_for_request(self, request: httpx.Request) -> httpcore.AsyncConnectionPool | httpcore.AsyncHTTPProxy:
        proxy = self._proxy_for_request(request)
        if proxy is None:
            return self._pool
        key = f"{proxy.url!s}|{proxy.raw_auth!r}|{proxy.headers!r}"
        if key not in self._proxy_pools:
            self._proxy_pools[key] = self._build_proxy_pool(proxy)
        return self._proxy_pools[key]

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
        response = await self._pool_for_request(request).handle_async_request(req)
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
        for pool in self._proxy_pools.values():
            await pool.aclose()


class _HttpcoreResponseStream(httpx.AsyncByteStream):
    def __init__(self, stream: Any):
        self._stream = stream

    async def __aiter__(self):
        async for chunk in self._stream:
            yield chunk

    async def aclose(self) -> None:
        await self._stream.aclose()
