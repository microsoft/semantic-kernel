# Copyright (c) Microsoft. All rights reserved.

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Sequence
from typing import Any
from urllib.parse import ParseResult, urlparse

from pydantic import Field

from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.kernel_pydantic import KernelBaseModel

DnsResolver = Callable[[str], Awaitable[Sequence[str | ipaddress.IPv4Address | ipaddress.IPv6Address]]]

DEFAULT_ALLOWED_SCHEME = "https"

# Azure instance metadata service (WireServer). Unlike the AWS/GCP equivalents, this
# address is publicly routable, so it would otherwise pass the private-address checks:
# 168.63.129.16 has is_private=False and is_link_local=False, so no generic rule
# catches it - not even after NAT64 decoding (64:ff9b::a83f:8110 decodes to exactly
# this address and would sail through the private/link-local branches). The explicit
# entry below is therefore load-bearing, not redundant with the range checks; do not
# remove it on the assumption that "the private-address branch already covers Azure
# metadata".
_AZURE_WIRE_SERVER = ipaddress.ip_address("168.63.129.16")
_AZURE_WIRE_SERVER_CATEGORY = "Azure metadata (WireServer)"

# NAT64 (RFC 6052) prefixes. The well-known prefix 64:ff9b::/96 has a fixed length
# (RFC 6052 section 2.1), so an embedded IPv4 always occupies the last 32 bits and can
# be decoded. The local-use prefix 64:ff9b:1::/48 (RFC 8215) has no fixed embedding
# length: RFC 6052 section 3.3 leaves the prefix length to translator configuration
# and it is not carried in the address, so the range is treated as non-public in its
# own right instead of guessing at its contents.
_NAT64_WELL_KNOWN_PREFIX = ipaddress.ip_network("64:ff9b::/96")
_NAT64_LOCAL_USE_PREFIX = ipaddress.ip_network("64:ff9b:1::/48")


class ServerUrlValidationOptions(KernelBaseModel):
    """Options for validating OpenAPI operation request URLs."""

    allowed_base_urls: list[str] = Field(default_factory=list)
    allow_private_network_access: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Validate configured allowed base URLs."""
        for allowed_base_url in self.allowed_base_urls:
            _parse_absolute_url(allowed_base_url, option_name="allowed_base_urls")


async def validate_server_url(
    url: str,
    options: ServerUrlValidationOptions | None = None,
    dns_resolver: DnsResolver | None = None,
) -> None:
    """Validate a fully resolved OpenAPI operation URL against the supplied policy."""
    options = options or ServerUrlValidationOptions()
    try:
        parsed_url = _parse_absolute_url(url)
    except ValueError as exc:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed because it is not a valid absolute URI."
        ) from exc

    if _matches_allowed_base_url(parsed_url, options.allowed_base_urls):
        return

    if options.allowed_base_urls:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed. It does not match any of the allowed base URLs."
        )

    if parsed_url.scheme.lower() != DEFAULT_ALLOWED_SCHEME:
        raise FunctionExecutionException(
            f"The request URI scheme '{parsed_url.scheme}' is not allowed. "
            f"Only '{DEFAULT_ALLOWED_SCHEME}' is permitted by default. "
            "To allow this URL, add it to server_url_validation_allowed_base_urls."
        )

    if options.allow_private_network_access:
        # Allowing access to a private network is not the same as allowing access to
        # the host agent's cloud metadata endpoint, which is always blocked.
        _reject_cloud_metadata_host(parsed_url)
        return

    await _ensure_public_host(parsed_url, dns_resolver)


def try_categorize_non_public_address(
    address: str | ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> tuple[bool, str]:
    """Return whether an IP address is non-public and the category when blocked."""
    ip_address = ipaddress.ip_address(address)

    if isinstance(ip_address, ipaddress.IPv6Address):
        if ip_address in _NAT64_LOCAL_USE_PREFIX:
            return True, "NAT64 local-use prefix (RFC 8215)"
        embedded_ipv4 = _extract_embedded_ipv4(ip_address)
        if embedded_ipv4 is not None:
            ip_address = embedded_ipv4
        elif ip_address.ipv4_mapped:
            ip_address = ip_address.ipv4_mapped

    if isinstance(ip_address, ipaddress.IPv4Address):
        return _try_classify_ipv4(ip_address)

    return _try_classify_ipv6(ip_address)


def _extract_embedded_ipv4(address: ipaddress.IPv6Address) -> ipaddress.IPv4Address | None:
    """Decode an IPv4 address embedded in an IPv6 address, if any.

    Covers IPv4-mapped (``::ffff:a.b.c.d``), 6to4 (``2002::/16``, RFC 3056), Teredo
    (``2001::/32``, RFC 4380) and NAT64 addresses embedded via the well-known
    ``64:ff9b::/96`` prefix (RFC 6052). The embedded IPv4 is classified separately so
    a private address cannot slip through an otherwise public-looking IPv6 address.
    The local-use ``64:ff9b:1::/48`` range (RFC 8215) is handled in
    :func:`try_categorize_non_public_address` as a non-public range rather than
    decoded, because its prefix length is not carried in the address.
    """
    if address.sixtofour is not None:
        return address.sixtofour
    if address.teredo is not None:
        _, teredo_client = address.teredo
        return teredo_client
    if address in _NAT64_WELL_KNOWN_PREFIX:
        return ipaddress.ip_address(address.packed[-4:])
    return None


def _parse_absolute_url(url: str, option_name: str = "url") -> ParseResult:
    parsed_url = urlparse(url)
    try:
        parsed_url.port
    except ValueError as exc:
        raise ValueError(f"Invalid {option_name}: {url}") from exc

    if not parsed_url.scheme or not parsed_url.netloc or not parsed_url.hostname:
        raise ValueError(f"Invalid {option_name}: {url}")
    return parsed_url


def _matches_allowed_base_url(url: ParseResult, allowed_base_urls: list[str]) -> bool:
    for allowed_base_url in allowed_base_urls:
        base_url = _parse_absolute_url(allowed_base_url, option_name="allowed_base_urls")
        if url.scheme.lower() != base_url.scheme.lower():
            continue
        if (url.hostname or "").lower() != (base_url.hostname or "").lower():
            continue
        if _effective_port(url) != _effective_port(base_url):
            continue
        if _matches_path_prefix(url.path, base_url.path):
            return True

    return False


def _effective_port(url: ParseResult) -> int | None:
    if url.port is not None:
        return url.port
    if url.scheme.lower() == "https":
        return 443
    if url.scheme.lower() == "http":
        return 80
    return None


def _matches_path_prefix(url_path: str, base_path: str) -> bool:
    url_path = url_path or "/"
    base_path = base_path or "/"

    if url_path.lower() == base_path.lower():
        return True

    base_path_with_slash = base_path if base_path.endswith("/") else f"{base_path}/"
    return url_path.lower().startswith(base_path_with_slash.lower())


async def _ensure_public_host(parsed_url: ParseResult, dns_resolver: DnsResolver | None) -> None:
    host = parsed_url.hostname
    if host is None:
        raise FunctionExecutionException(f"The request URI '{parsed_url.geturl()}' does not contain a valid host.")

    try:
        ip_address = ipaddress.ip_address(host)
    except ValueError:
        addresses = await _resolve_host(host, dns_resolver)
    else:
        _ensure_public_address(parsed_url.geturl(), ip_address)
        return

    if not addresses:
        raise FunctionExecutionException(
            f"The request URI '{parsed_url.geturl()}' is not allowed: DNS resolution for host "
            f"'{host}' returned no addresses. The request is blocked as a precaution."
        )

    for address in addresses:
        _ensure_public_address(parsed_url.geturl(), address)


async def _resolve_host(
    host: str,
    dns_resolver: DnsResolver | None,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        if dns_resolver:
            resolved_addresses = await dns_resolver(host)
            return [ipaddress.ip_address(address) for address in resolved_addresses]

        loop = asyncio.get_running_loop()
        addr_info = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (OSError, ValueError) as exc:
        raise FunctionExecutionException(
            f"The request URI host '{host}' is not allowed: DNS resolution failed. "
            "The request is blocked as a precaution to prevent potential access to private network addresses."
        ) from exc

    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    seen_addresses: set[str] = set()
    for family, _, _, _, sockaddr in addr_info:
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        address = ipaddress.ip_address(sockaddr[0])
        address_string = str(address)
        if address_string not in seen_addresses:
            addresses.append(address)
            seen_addresses.add(address_string)
    return addresses


def _ensure_public_address(url: str, address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    blocked, category = try_categorize_non_public_address(address)
    if blocked:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed: host resolves to a {category} address ({address}), "
            "which is blocked by default to prevent Server-Side Request Forgery (SSRF). "
            "To allow this URL, add it to server_url_validation_allowed_base_urls or set "
            "allow_private_network_access=True."
        )


def _reject_cloud_metadata_host(parsed_url: ParseResult) -> None:
    """Block cloud metadata endpoints even when private network access is allowed.

    Only literal IP hosts are checked: private-network mode deliberately does not
    resolve hostnames, so a hostname pointing at a metadata endpoint is out of scope.
    """
    host = parsed_url.hostname
    if host is None:
        return

    try:
        ip_address = ipaddress.ip_address(host)
    except ValueError:
        return

    blocked, category = try_categorize_non_public_address(ip_address)
    if blocked and category == _AZURE_WIRE_SERVER_CATEGORY:
        raise FunctionExecutionException(
            f"The request URI '{parsed_url.geturl()}' is not allowed: the host is the Azure "
            f"metadata endpoint (WireServer, {ip_address}), which is blocked even when "
            "allow_private_network_access=True to prevent SSRF against cloud metadata services."
        )


def _try_classify_ipv4(address: ipaddress.IPv4Address) -> tuple[bool, str]:
    b0, b1, b2, _ = address.packed

    if address == _AZURE_WIRE_SERVER:
        return True, _AZURE_WIRE_SERVER_CATEGORY
    if b0 == 0:
        return True, "unspecified"
    if b0 == 10:
        return True, "private (RFC1918)"
    if b0 == 127:
        return True, "loopback"
    if b0 == 169 and b1 == 254:
        return True, "link-local"
    if b0 == 172 and 16 <= b1 <= 31:
        return True, "private (RFC1918)"
    if b0 == 192 and b1 == 168:
        return True, "private (RFC1918)"
    if b0 == 100 and 64 <= b1 <= 127:
        return True, "carrier-grade NAT"
    if b0 == 198 and b1 in (18, 19):
        return True, "benchmarking"
    if b0 == 192 and b1 == 0 and b2 in (0, 2):
        return True, "reserved"
    if b0 == 198 and b1 == 51 and b2 == 100:
        return True, "reserved"
    if b0 == 203 and b1 == 0 and b2 == 113:
        return True, "reserved"
    if 224 <= b0 <= 239:
        return True, "multicast"
    if b0 >= 240:
        return True, "reserved"

    return False, ""


def _try_classify_ipv6(address: ipaddress.IPv6Address) -> tuple[bool, str]:
    if address.is_loopback:
        return True, "loopback"
    if address.is_unspecified:
        return True, "unspecified"
    if address.is_link_local:
        return True, "link-local"
    if address in ipaddress.ip_network("fc00::/7"):
        return True, "private (IPv6 ULA)"
    if address.is_multicast:
        return True, "multicast"
    if address in ipaddress.ip_network("2001:db8::/32"):
        return True, "reserved"

    return False, ""

