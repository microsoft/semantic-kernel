# Copyright (c) Microsoft. All rights reserved.

import ipaddress
import socket

import pytest

from semantic_kernel.connectors.openapi_plugin.server_url_validator import (
    ServerUrlValidationOptions,
    validate_server_url,
)
from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.utils.public_network_address_validator import try_categorize_non_public_address


@pytest.mark.parametrize(
    ("address", "expected_category"),
    [
        ("127.0.0.1", "loopback"),
        ("127.255.255.254", "loopback"),
        ("169.254.169.254", "link-local"),
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
        ("febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "link-local"),
        ("fec0::", "site-local"),
        ("fec0::1", "site-local"),
        ("feff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "site-local"),
        ("fc00::1", "private (IPv6 ULA)"),
        ("fd00::1", "private (IPv6 ULA)"),
        ("ff00::", "multicast"),
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
        await validate_server_url("https://169.254.169.254/latest/meta-data/")


async def test_validate_server_url_rejects_literal_loopback_ipv6():
    with pytest.raises(FunctionExecutionException, match="loopback"):
        await validate_server_url("https://[::1]/")


@pytest.mark.parametrize("address", ["fec0::", "fec0::1", "feff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"])
async def test_validate_server_url_rejects_literal_site_local_ipv6(address):
    with pytest.raises(FunctionExecutionException, match="site-local"):
        await validate_server_url(f"https://[{address}]/")


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


async def test_validate_server_url_preserves_explicit_hostname_allowlist_dns_bypass():
    options = ServerUrlValidationOptions(allowed_base_urls=["http://trusted.example.com/v1"])

    async def unexpected_resolver(host: str):
        raise AssertionError("An explicitly trusted URL should not be resolved.")

    await validate_server_url("http://trusted.example.com/v1/orders", options, dns_resolver=unexpected_resolver)


async def test_validate_server_url_rejects_when_allowed_base_urls_do_not_match():
    options = ServerUrlValidationOptions(allowed_base_urls=["https://api.example.com/v1"])

    with pytest.raises(FunctionExecutionException, match="allowed base URLs"):
        await validate_server_url("https://api.example.com/v2/orders", options)


@pytest.mark.parametrize("url", ["https://10.0.0.5/", "https://[fec0::1]/"])
async def test_validate_server_url_allows_private_network_access_after_scheme_gate(url):
    options = ServerUrlValidationOptions(allow_private_network_access=True)

    await validate_server_url(url, options)


@pytest.mark.parametrize(
    ("address", "expected_category"),
    [
        ("169.254.169.254", "link-local"),
        ("fec0::", "site-local"),
        ("fec0::1", "site-local"),
        ("feff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "site-local"),
    ],
)
async def test_validate_server_url_blocks_hostname_resolving_to_non_public_address(address, expected_category):
    async def fake_resolver(host: str):
        assert host == "evil.example.com"
        return [address]

    with pytest.raises(FunctionExecutionException, match=expected_category):
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


@pytest.mark.parametrize(
    "addresses",
    [
        ["93.184.216.34", "198.41.0.4"],
        ["2606:4700:4700::1111", "93.184.216.34", "2606:4700:4700::1001"],
    ],
)
async def test_validate_server_url_returns_validated_addresses_for_pinning(addresses):
    async def fake_resolver(host: str):
        assert host == "api.example.com"
        return addresses

    assert await validate_server_url("https://api.example.com/", dns_resolver=fake_resolver) == [
        ipaddress.ip_address(address) for address in addresses
    ]


async def test_validate_server_url_returns_validated_ipv6_address_for_pinning():
    async def fake_resolver(host: str):
        assert host == "api.example.com"
        return ["2606:2800:220:1:248:1893:25c8:1946"]

    assert await validate_server_url("https://api.example.com/", dns_resolver=fake_resolver) == [
        ipaddress.ip_address("2606:2800:220:1:248:1893:25c8:1946")
    ]


@pytest.mark.parametrize("host", ["93.184.216.34", "[2606:4700:4700::1111]"])
async def test_validate_server_url_returns_no_addresses_for_literal_ip_host(host):
    assert await validate_server_url(f"https://{host}/api") == []


async def test_validate_server_url_returns_no_addresses_for_allowed_base_url():
    options = ServerUrlValidationOptions(allowed_base_urls=["http://api.example.com"])
    assert await validate_server_url("http://api.example.com/api", options) == []


async def test_validate_server_url_returns_no_addresses_when_private_access_is_allowed():
    options = ServerUrlValidationOptions(allow_private_network_access=True)
    assert await validate_server_url("https://internal.example/api", options) == []
