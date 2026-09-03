# Copyright (c) Microsoft. All rights reserved.

import ipaddress
import socket
from collections import OrderedDict
from unittest.mock import MagicMock

import httpcore
import httpx
import pytest

from semantic_kernel.connectors.openapi_plugin.openapi_runner import OpenApiRunner
from semantic_kernel.connectors.openapi_plugin.server_url_validator import (
    ServerUrlValidationOptions,
    try_categorize_non_public_address,
)

HOST = "rebind.example"
PUBLIC_ADDRESS = "93.184.216.34"
SECOND_PUBLIC_ADDRESS = "198.41.0.4"
REBOUND_ADDRESS = "169.254.169.254"
PUBLIC_IPV6_ADDRESS = "2606:2800:220:1:248:1893:25c8:1946"

RAW_RESPONSE = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 13\r\n\r\nresponse text"


def build_runner(url: str, options: ServerUrlValidationOptions | None = None) -> tuple[OpenApiRunner, MagicMock]:
    """Build a runner whose operation resolves to `url` and carries no payload."""
    runner = OpenApiRunner({}, server_url_validation_options=options)
    operation = MagicMock()
    operation.method = "GET"
    operation.build_headers.return_value = {}
    operation.responses = OrderedDict()
    runner.build_operation_url = MagicMock(return_value=url)
    runner.build_operation_payload = MagicMock(return_value=(None, None))
    return runner, operation


def static_getaddrinfo(host_name: str, addresses: list[str]):
    """Return a `socket.getaddrinfo` replacement that answers `host_name` with `addresses`."""
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, port=None, *args, **kwargs):
        if host == host_name:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port or 0)) for address in addresses]
        return real_getaddrinfo(host, port, *args, **kwargs)

    return fake_getaddrinfo


def rebinding_getaddrinfo(host_name: str, first_address: str, later_address: str, lookups: list[str]):
    """Return a `socket.getaddrinfo` replacement that answers `host_name` differently after the first lookup."""
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, port=None, *args, **kwargs):
        if host == host_name:
            lookups.append(host)
            address = first_address if len(lookups) == 1 else later_address
            family = socket.AF_INET6 if ":" in address else socket.AF_INET
            return [(family, socket.SOCK_STREAM, 6, "", (address, port or 0))]
        return real_getaddrinfo(host, port, *args, **kwargs)

    return fake_getaddrinfo


class RecordingStream(httpcore.AsyncMockStream):
    """A mock network stream that records the TLS SNI hostname and the bytes written to the wire."""

    def __init__(self, buffer: list[bytes], record: dict) -> None:
        super().__init__(buffer)
        self._record = record

    async def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self._record["written"] += buffer

    async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        self._record["sni_hostname"] = server_hostname
        return self


class RecordingBackend(httpcore.AsyncNetworkBackend):
    """A network backend that records the address the connection is actually opened against.

    A real backend resolves a hostname at connect time, which is exactly the second, unvalidated
    lookup this test grid is about, so hostnames are resolved here the same way.
    """

    def __init__(self, record: dict) -> None:
        self._record = record

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        try:
            ipaddress.ip_address(host)
        except ValueError:
            connect_target = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)[0][4][0]
        else:
            connect_target = host
        self._record["connect_target"] = connect_target
        return RecordingStream([RAW_RESPONSE], self._record)


def install_recording_client(monkeypatch) -> dict:
    """Make the runner's built-in client speak to a recording backend through real httpx machinery."""
    record: dict = {"written": b"", "connect_target": None, "sni_hostname": None}
    real_client_type = httpx.AsyncClient

    def client_factory(**kwargs):
        transport = httpx.AsyncHTTPTransport()
        # httpx exposes no public seam for the network backend, so the test reaches into the
        # transport's pool. Everything above it (URL handling, headers, extensions) is real.
        transport._pool._network_backend = RecordingBackend(record)
        return real_client_type(transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    return record


def install_capturing_client(monkeypatch, responses: list | None = None) -> list[httpx.Request]:
    """Make the runner's built-in client capture the request it sends instead of connecting."""
    requests: list[httpx.Request] = []
    real_client_type = httpx.AsyncClient
    outcomes = list(responses or [])

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        outcome = outcomes.pop(0) if outcomes else None
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(200, text="response text")

    def client_factory(**kwargs):
        return real_client_type(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    return requests


async def test_run_operation_pins_connection_to_validated_address_under_dns_rebinding(monkeypatch):
    """A host that resolves public at validation time and private at connect time must not be reached."""
    lookups: list[str] = []
    monkeypatch.setattr(socket, "getaddrinfo", rebinding_getaddrinfo(HOST, PUBLIC_ADDRESS, REBOUND_ADDRESS, lookups))
    record = install_recording_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}/api/op")

    assert await runner.run_operation(operation, {}, None) == "response text"

    assert record["connect_target"] == PUBLIC_ADDRESS, (
        f"connection was opened against {record['connect_target']}, not the validated address"
    )
    assert try_categorize_non_public_address(record["connect_target"]) == (False, "")
    assert record["sni_hostname"] == HOST
    assert b"Host: rebind.example\r\n" in record["written"]
    assert len(lookups) == 1, "the host was resolved a second time at connect time"


async def test_run_operation_pins_request_url_and_preserves_host_identity(monkeypatch):
    """The request is addressed to the validated IP while keeping the original Host and SNI."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}/api/op?a=1")

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == f"https://{PUBLIC_ADDRESS}/api/op?a=1"
    assert requests[0].headers["Host"] == HOST
    assert requests[0].extensions["sni_hostname"] == HOST


async def test_run_operation_pins_first_validated_address_when_several_are_returned(monkeypatch):
    """Pinning uses the resolver's preferred address, not an arbitrary one."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS, SECOND_PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}/api/op")

    await runner.run_operation(operation, {}, None)

    assert len(requests) == 1
    assert requests[0].url.host == PUBLIC_ADDRESS


async def test_run_operation_falls_back_to_the_next_validated_address_on_connect_error(monkeypatch):
    """A connection failure falls through to the remaining validated addresses, as the resolver would."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS, SECOND_PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch, responses=[httpx.ConnectError("no route")])
    runner, operation = build_runner(f"https://{HOST}/api/op")

    assert await runner.run_operation(operation, {}, None) == "response text"

    assert [request.url.host for request in requests] == [PUBLIC_ADDRESS, SECOND_PUBLIC_ADDRESS]


async def test_run_operation_does_not_retry_a_request_that_may_already_have_been_delivered(monkeypatch):
    """Only connection failures fall through. A later failure means the request may already be on the wire."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS, SECOND_PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch, responses=[httpx.ReadTimeout("timed out")])
    runner, operation = build_runner(f"https://{HOST}/api/op")

    with pytest.raises(httpx.ReadTimeout):
        await runner.run_operation(operation, {}, None)

    assert [request.url.host for request in requests] == [PUBLIC_ADDRESS], (
        "a request that may already have been delivered was resent to a second address"
    )


async def test_run_operation_brackets_ipv6_address_and_preserves_the_port(monkeypatch):
    """An IPv6 pin keeps the URL parseable and does not move the request to another port."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_IPV6_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}:8443/api/op")

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == f"https://[{PUBLIC_IPV6_ADDRESS}]:8443/api/op"
    assert requests[0].url.port == 8443
    assert requests[0].headers["Host"] == f"{HOST}:8443"
    assert requests[0].extensions["sni_hostname"] == HOST


async def test_run_operation_does_not_pin_when_an_allowed_base_url_matches(monkeypatch):
    """The allowed-base-url path never resolves the host, so there is no vetted address to pin."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo("api.example.com", [PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(
        "https://api.example.com/api/op",
        ServerUrlValidationOptions(allowed_base_urls=["https://api.example.com"]),
    )

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == "https://api.example.com/api/op"
    assert "sni_hostname" not in requests[0].extensions


async def test_run_operation_does_not_pin_when_private_network_access_is_allowed(monkeypatch):
    """Opting into private network access skips resolution, so nothing may be pinned."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo("internal.example", ["10.0.0.5"]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(
        "https://internal.example/api/op",
        ServerUrlValidationOptions(allow_private_network_access=True),
    )

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == "https://internal.example/api/op"
    assert "sni_hostname" not in requests[0].extensions


async def test_run_operation_does_not_pin_a_literal_ip_host(monkeypatch):
    """A literal address cannot be rebound, so the request is left exactly as it was."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{PUBLIC_ADDRESS}/api/op")

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == f"https://{PUBLIC_ADDRESS}/api/op"
    assert requests[0].headers["Host"] == PUBLIC_ADDRESS
    assert "sni_hostname" not in requests[0].extensions


async def test_run_operation_does_not_pin_when_an_environment_proxy_is_configured(monkeypatch):
    """A proxy resolves the target name itself, so a locally resolved address must not be forced on it."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS]))
    monkeypatch.setattr(
        "semantic_kernel.connectors.openapi_plugin.openapi_runner.getproxies",
        lambda: {"https": "http://proxy.example:8080"},
    )
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}/api/op")

    await runner.run_operation(operation, {}, None)

    assert str(requests[0].url) == f"https://{HOST}/api/op"
    assert "sni_hostname" not in requests[0].extensions


async def test_run_operation_does_not_pin_a_caller_supplied_client(monkeypatch):
    """A caller-supplied client owns its transport, so its requests are left untouched."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [PUBLIC_ADDRESS]))
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, text="response text")

    runner, operation = build_runner(f"https://{HOST}/api/op")
    runner.http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    await runner.run_operation(operation, {}, None)
    await runner.http_client.aclose()

    assert str(requests[0].url) == f"https://{HOST}/api/op"
    assert "sni_hostname" not in requests[0].extensions


async def test_run_operation_still_blocks_a_host_that_resolves_to_a_private_address(monkeypatch):
    """Pinning must not weaken the existing block on non-public resolutions."""
    monkeypatch.setattr(socket, "getaddrinfo", static_getaddrinfo(HOST, [REBOUND_ADDRESS]))
    requests = install_capturing_client(monkeypatch)
    runner, operation = build_runner(f"https://{HOST}/api/op")

    with pytest.raises(Exception, match="link-local"):
        await runner.run_operation(operation, {}, None)

    assert requests == []
