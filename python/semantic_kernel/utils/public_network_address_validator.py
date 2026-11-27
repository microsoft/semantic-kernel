# Copyright (c) Microsoft. All rights reserved.

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Sequence
from urllib.parse import ParseResult

from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException

DnsResolver = Callable[[str], Awaitable[Sequence[str | ipaddress.IPv4Address | ipaddress.IPv6Address]]]

_AZURE_WIRESERVER = ipaddress.IPv4Address("168.63.129.16")

# RFC 6052 only puts the embedded IPv4 address in the last four bytes for a /96, which is the only
# length the well-known prefix allows. The RFC 8215 local-use prefix has a translator-specific length,
# so its embedded address cannot be read from the address itself (the shorter lengths put a suffix in
# those bytes, and decoding that reads 0.0.0.0 out of an ordinary target). It is blocked as a whole
# instead of decoded at a guessed length.
_NAT64_WELL_KNOWN_NETWORK = ipaddress.IPv6Network("64:ff9b::/96")
_NAT64_LOCAL_USE_NETWORK = ipaddress.IPv6Network("64:ff9b:1::/48")


def try_categorize_non_public_address(
    address: str | ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> tuple[bool, str]:
    """Return whether an IP address is non-public and the category when blocked."""
    ip_address = ipaddress.ip_address(address)

    if isinstance(ip_address, ipaddress.IPv6Address) and ip_address.ipv4_mapped:
        ip_address = ip_address.ipv4_mapped

    if isinstance(ip_address, ipaddress.IPv4Address):
        return _try_classify_ipv4(ip_address)

    return _try_classify_ipv6(ip_address)


async def ensure_public_host(
    parsed_url: ParseResult,
    dns_resolver: DnsResolver | None = None,
    configuration_hint: str = "",
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Reject non-public destinations and return vetted DNS addresses in resolver order.

    The caller is responsible for binding the returned addresses to the connection.
    Literal IP hosts are validated but return an empty list because there is no DNS lookup to pin.
    """
    host = parsed_url.hostname
    if host is None:
        raise FunctionExecutionException(f"The request URI '{parsed_url.geturl()}' does not contain a valid host.")

    try:
        ip_address = ipaddress.ip_address(host)
    except ValueError:
        addresses = await _resolve_host(host, dns_resolver)
    else:
        _ensure_public_address(parsed_url.geturl(), ip_address, configuration_hint)
        return []

    if not addresses:
        raise FunctionExecutionException(
            f"The request URI '{parsed_url.geturl()}' is not allowed: DNS resolution for host "
            f"'{host}' returned no addresses. The request is blocked as a precaution."
        )

    for address in addresses:
        _ensure_public_address(parsed_url.geturl(), address, configuration_hint)
    return addresses


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


def _ensure_public_address(
    url: str,
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
    configuration_hint: str,
) -> None:
    blocked, category = try_categorize_non_public_address(address)
    if blocked:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed: host resolves to a {category} address ({address}), "
            "which is blocked by default to prevent Server-Side Request Forgery (SSRF). "
            f"{configuration_hint}"
        )


def _try_classify_ipv4(address: ipaddress.IPv4Address) -> tuple[bool, str]:
    b0, b1, b2, _ = address.packed

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
    if address == _AZURE_WIRESERVER:
        # Publicly routable, so no range check above reaches it, yet it is the Azure host agent's
        # credential endpoint and is reachable from every Azure VM.
        return True, "cloud metadata (Azure WireServer)"

    return False, ""


def _embedded_ipv4(address: ipaddress.IPv6Address) -> ipaddress.IPv4Address | None:
    """Return the IPv4 address a NAT64, 6to4 or Teredo IPv6 address carries, if it is one of those forms.

    `sixtofour` and `teredo` return None outside their own prefixes, and Teredo's client address is
    stored with its bits inverted (RFC 4380), which the standard library undoes.
    """
    if address in _NAT64_WELL_KNOWN_NETWORK:
        return ipaddress.IPv4Address(address.packed[12:])
    if address.sixtofour is not None:
        return address.sixtofour
    if address.teredo is not None:
        return address.teredo[1]
    return None


def _try_classify_ipv6(address: ipaddress.IPv6Address) -> tuple[bool, str]:
    if address.is_loopback:
        return True, "loopback"
    if address.is_unspecified:
        return True, "unspecified"
    if address.is_link_local:
        return True, "link-local"
    if address.is_site_local:
        return True, "site-local"
    if address in ipaddress.ip_network("fc00::/7"):
        return True, "private (IPv6 ULA)"
    if address.is_multicast:
        return True, "multicast"
    if address in ipaddress.ip_network("2001:db8::/32"):
        return True, "reserved"
    if address in _NAT64_LOCAL_USE_NETWORK:
        return True, "NAT64 local-use prefix"

    # NAT64, 6to4 and Teredo carry an IPv4 target inside an IPv6 address that looks public, so
    # classify the IPv4 it names.
    embedded = _embedded_ipv4(address)
    if embedded is not None:
        blocked, category = _try_classify_ipv4(embedded)
        if blocked:
            return True, f"{category} (embedded in IPv6)"

    return False, ""
