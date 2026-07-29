# Copyright (c) Microsoft. All rights reserved.

import ipaddress
import socket

import pytest
from pytest import raises

from semantic_kernel.connectors.openapi_plugin.server_url_validator import (
    ServerUrlValidationOptions,
    try_categorize_non_public_address,
    validate_server_url,
)
from semantic_kernel.exceptions import FunctionExecutionException


@pytest.mark.parametrize(
    ("address", "expected_category"),
    [
        ("127.0.0.1", "loopback"),
        ("127.255.255.254", "loopback"),
        ("169.254.10.10", "link-local"),
        ("169.254.0.1", "link-local"),
        ("10.0.0.1", "private (RFC1918)"),
        ("172.16.0.1", "private (RFC1918)"),
        ("172.31.255.255", "private (RFC1918)"),
        ("192.168.0.1", "private (RFC1918)"),
        ("100.64.0.1", "carrier-grade NAT"),
        ("100.127.255.254", "carrier-grade NAT"),
        ("0.0.0.0", "unspecified"),
        ("224.0.0.1", "multicast"),
        ("239.255.255.255", "multicast"),
        ("240.0.0.1", "reserved"),
        ("255.255.255.255", "reserved"),
        ("198.18.0.1", "benchmarking"),
        ("192.0.2.1", "reserved"),
        ("198.51.100.1", "reserved"),
        ("203.0.113.1", "reserved"),
        ("::1", "loopback"),
        ("::", "unspecified"),
        ("fe80::1", "link-local"),
        ("fc00::1", "private (IPv6 ULA)"),
        ("fd00::1", "private (IPv6 ULA)"),
        ("ff02::1", "multicast"),
        ("2001:db8::1", "reserved"),
        ("::ffff:127.0.0.1", "loopback"),
        ("::ffff:169.254.169.254", "link-local"),
    ],
)
def test_try_categorize_non_public_address(address: str, expected_category: str):
    blocked, category = try_categorize_non_public_address(address)

    assert blocked is True
    assert category == expected_category


@pytest.mark.parametrize(
    "address",
    [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",
        "172.15.255.255",
        "172.32.0.1",
        "11.0.0.1",
        "192.169.0.1",
        "100.63.255.255",
        "100.128.0.1",
        "2606:4700:4700::1111",
    ],
)
def test_try_categorize_non_public_address_allows_public_addresses(address: str):
    blocked, category = try_categorize_non_public_address(address)

    assert blocked is False
    assert category == ""


async def test_validate_server_url_rejects_literal_link_local_ipv4():
    with pytest.raises(FunctionExecutionException, match="link-local"):
        await validate_server_url("https://169.254.10.10/latest/meta-data/")


async def test_validate_server_url_rejects_literal_loopback_ipv6():
    with pytest.raises(FunctionExecutionException, match="loopback"):
        await validate_server_url("https://[::1]/")


async def test_validate_server_url_rejects_http_scheme_by_default():
    with pytest.raises(FunctionExecutionException, match="scheme"):
        await validate_server_url("http://api.example.com/")


async def test_validate_server_url_allows_public_https_literal_by_default():
    await validate_server_url("https://1.1.1.1/")


async def test_validate_server_url_rejects_invalid_uri_with_function_execution_exception():
    with pytest.raises(FunctionExecutionException, match="not a valid absolute URI"):
        await validate_server_url("invalid_url")


async def test_validate_server_url_allows_explicit_base_url_for_private_http_address():
    options = ServerUrlValidationOptions(allowed_base_urls=["http://192.168.1.100/v1"])

    await validate_server_url("http://192.168.1.100/v1/orders", options)


async def test_validate_server_url_rejects_when_allowed_base_urls_do_not_match():
    options = ServerUrlValidationOptions(allowed_base_urls=["https://api.example.com/v1"])

    with pytest.raises(FunctionExecutionException, match="allowed base URLs"):
        await validate_server_url("https://api.example.com/v2/orders", options)


async def test_validate_server_url_allows_private_network_access_after_scheme_gate():
    options = ServerUrlValidationOptions(allow_private_network_access=True)

    await validate_server_url("https://10.0.0.5/", options)


async def test_validate_server_url_blocks_hostname_resolving_to_link_local():
    async def fake_resolver(host: str):
        assert host == "evil.example.com"
        return ["169.254.10.10"]

    with pytest.raises(FunctionExecutionException, match="link-local"):
        await validate_server_url("https://evil.example.com/latest/meta-data/", dns_resolver=fake_resolver)


async def test_validate_server_url_blocks_hostname_resolving_to_loopback():
    async def fake_resolver(host: str):
        assert host == "attacker.example.com"
        return ["127.0.0.1"]

    with pytest.raises(FunctionExecutionException, match="loopback"):
        await validate_server_url("https://attacker.example.com/api", dns_resolver=fake_resolver)


async def test_validate_server_url_blocks_when_any_resolved_address_is_private():
    async def fake_resolver(host: str):
        assert host == "rebind.example.com"
        return ["93.184.216.34", "10.0.0.1"]

    with pytest.raises(FunctionExecutionException, match="private"):
        await validate_server_url("https://rebind.example.com/", dns_resolver=fake_resolver)


async def test_validate_server_url_allows_hostname_resolving_to_public_ip():
    async def fake_resolver(host: str):
        assert host == "api.example.com"
        return ["93.184.216.34"]

    await validate_server_url("https://api.example.com/", dns_resolver=fake_resolver)


async def test_validate_server_url_blocks_dns_resolution_failure():
    async def fake_resolver(host: str):
        assert host == "unreachable.example.com"
        raise socket.gaierror()

    with pytest.raises(FunctionExecutionException, match="DNS resolution"):
        await validate_server_url("https://unreachable.example.com/", dns_resolver=fake_resolver)


async def test_validate_server_url_blocks_empty_dns_response():
    async def fake_resolver(host: str):
        assert host == "empty-dns.example.com"
        return []

    with pytest.raises(FunctionExecutionException, match="returned no addresses"):
        await validate_server_url("https://empty-dns.example.com/", dns_resolver=fake_resolver)


CLOUD_METADATA_ENDPOINTS = [
    "169.254.169.254",  # AWS IMDS, GCP, Azure, OCI, DigitalOcean
    "169.254.170.2",  # AWS ECS task IAM role credentials
    "169.254.170.23",  # AWS EKS Pod Identity Agent
    "168.63.129.16",  # Azure WireServer (publicly routable)
    "100.100.100.200",  # Alibaba Cloud
    "192.0.0.192",  # Oracle Cloud (Classic)
    "169.254.42.42",  # Scaleway
]


@pytest.mark.parametrize("address", CLOUD_METADATA_ENDPOINTS)
async def test_cloud_metadata_endpoints_blocked(address):
    with raises(FunctionExecutionException):
        await validate_server_url(f"https://{address}/latest/meta-data/")


@pytest.mark.parametrize("address", CLOUD_METADATA_ENDPOINTS)
async def test_cloud_metadata_endpoints_blocked_with_private_access(address):
    """`allow_private_network_access` covers your own network, not the credential endpoint."""
    options = ServerUrlValidationOptions(allow_private_network_access=True)
    with raises(FunctionExecutionException, match="cloud metadata endpoint"):
        await validate_server_url(f"https://{address}/latest/meta-data/", options)


async def test_private_network_access_still_permits_rfc1918():
    options = ServerUrlValidationOptions(allow_private_network_access=True)
    await validate_server_url("https://10.0.0.5/resource", options)


async def test_private_network_access_still_permits_loopback():
    options = ServerUrlValidationOptions(allow_private_network_access=True)
    await validate_server_url("https://127.0.0.1/resource", options)


@pytest.mark.parametrize(
    "address",
    [
        "64:ff9b::169.254.169.254",  # NAT64 well-known prefix (RFC 6052)
        "64:ff9b:1::169.254.169.254",  # NAT64 local-use prefix (RFC 8215)
        "2002:a9fe:a9fe::",  # 6to4 (RFC 3056)
        "::ffff:169.254.169.254",  # IPv4-mapped
    ],
)
async def test_ipv6_forms_carrying_a_blocked_ipv4_are_rejected(address):
    with raises(FunctionExecutionException):
        await validate_server_url(f"https://[{address}]/latest/meta-data/")


async def test_teredo_carrying_a_blocked_ipv4_is_rejected():
    """Teredo obfuscates the client IPv4 by XOR-ing the low 32 bits with all ones."""
    target = ipaddress.IPv4Address("169.254.169.254")
    low = bytes(byte ^ 0xFF for byte in target.packed)
    teredo = ipaddress.IPv6Address(b"\x20\x01\x00\x00" + b"\x00" * 8 + low)

    with raises(FunctionExecutionException):
        await validate_server_url(f"https://[{teredo}]/latest/meta-data/")


@pytest.mark.parametrize(
    "address",
    [
        "64:ff9b::1.1.1.1",  # NAT64 pointing at a public IPv4
        "64:ff9b:1::1.1.1.1",
        "2002:0101:0101::",  # 6to4 pointing at 1.1.1.1
        "2606:4700:4700::1111",  # plain public IPv6
    ],
)
async def test_ipv6_forms_carrying_a_public_ipv4_are_allowed(address):
    """Decoding must not reject legitimate NAT64/6to4 targets."""
    await validate_server_url(f"https://[{address}]/resource")
