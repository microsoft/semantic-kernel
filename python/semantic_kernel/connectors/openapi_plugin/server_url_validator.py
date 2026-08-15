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

# Cloud metadata / credential endpoints. Most fall inside ranges `_try_classify_ipv4` already
# rejects, but `168.63.129.16` (Azure WireServer) is publicly routable, so no range check reaches
# it. They are listed explicitly and checked even when `allow_private_network_access` is set:
# reaching a host on your own network and reaching the instance's credential endpoint are
# different requests, and only the first is what that option is for.
CLOUD_METADATA_ADDRESSES: frozenset[ipaddress.IPv4Address | ipaddress.IPv6Address] = frozenset(
    ipaddress.ip_address(address)
    for address in (
        "169.254.169.254",  # AWS IMDS, GCP, Azure, OCI, DigitalOcean, Hetzner, OpenStack
        "169.254.170.2",  # AWS ECS task IAM role credentials
        "169.254.170.23",  # AWS EKS Pod Identity Agent
        "168.63.129.16",  # Azure WireServer / platform channel (publicly routable)
        "100.100.100.200",  # Alibaba Cloud
        "192.0.0.192",  # Oracle Cloud (Classic)
        "169.254.42.42",  # Scaleway
        "fd00:ec2::254",  # AWS IMDS over IPv6
        "fd00:ec2::23",  # AWS EKS Pod Identity Agent over IPv6
    )
)

# NAT64 (RFC 6052) and 6to4 (RFC 3056) carry an IPv4 address inside the IPv6 one. Only the /96
# embedding is decoded: it is the only length the well-known prefix allows, and guessing the
# shorter lengths inside the RFC 8215 local-use prefix reads bytes that are not the embedded
# address, which would reject legitimate NAT64 targets.
_NAT64_IPV4_OFFSETS = (12, 13, 14, 15)
_SIXTOFOUR_OFFSETS = (2, 3, 4, 5)
_NAT64_NETWORKS: tuple[ipaddress.IPv6Network, ...] = (ipaddress.IPv6Network("64:ff9b::/96"),)
# RFC 8215 local-use space, where the translator's prefix length is configuration rather than
# anything the address carries (RFC 6052 section 3.3). Bytes 12-15 hold the embedded address only
# for a /96; for the shorter lengths they hold the suffix, which the RFC says SHOULD be zero, so
# decoding them here reads 0.0.0.0 out of a perfectly ordinary target. Blocking the prefix whole
# avoids guessing in either direction: no public host is rejected as "unspecified", and no
# metadata address reaches the fit check through a length this code cannot determine.
_NAT64_LOCAL_USE_NETWORK = ipaddress.IPv6Network("64:ff9b:1::/48")
_SIXTOFOUR_NETWORK = ipaddress.IPv6Network("2002::/16")
_TEREDO_NETWORK = ipaddress.IPv6Network("2001::/32")


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

    await _ensure_public_host(
        parsed_url, dns_resolver, allow_private_network_access=options.allow_private_network_access
    )


def is_cloud_metadata_address(address: str | ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return whether an address, or an IPv4 embedded in it, is a cloud metadata endpoint."""
    ip_address = ipaddress.ip_address(address)
    if ip_address in CLOUD_METADATA_ADDRESSES:
        return True
    return any(embedded in CLOUD_METADATA_ADDRESSES for embedded in _embedded_ipv4s(ip_address))


def try_categorize_non_public_address(
    address: str | ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> tuple[bool, str]:
    """Return whether an IP address is non-public and the category when blocked."""
    ip_address = ipaddress.ip_address(address)

    if isinstance(ip_address, ipaddress.IPv6Address) and ip_address.ipv4_mapped:
        ip_address = ip_address.ipv4_mapped

    if isinstance(ip_address, ipaddress.IPv4Address):
        return _try_classify_ipv4(ip_address)

    blocked, category = _try_classify_ipv6(ip_address)
    if blocked:
        return blocked, category

    # 6to4, NAT64 and Teredo carry an IPv4 target inside an otherwise public-looking IPv6
    # address. Decode those and classify the IPv4 they name.
    for embedded in _embedded_ipv4s(ip_address):
        blocked, category = _try_classify_ipv4(embedded)
        if blocked:
            return blocked, f"{category} (embedded in IPv6)"

    return False, ""


def _embedded_ipv4s(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> list[ipaddress.IPv4Address]:
    """Decode the IPv4 addresses carried inside IPv4-mapped, NAT64, 6to4 and Teredo IPv6 forms."""
    if not isinstance(address, ipaddress.IPv6Address):
        return []

    packed = address.packed
    candidates: list[ipaddress.IPv4Address] = []

    if address.ipv4_mapped is not None:
        candidates.append(address.ipv4_mapped)

    if any(address in network for network in _NAT64_NETWORKS):
        candidates.append(ipaddress.IPv4Address(bytes(packed[offset] for offset in _NAT64_IPV4_OFFSETS)))

    if address in _SIXTOFOUR_NETWORK:
        candidates.append(ipaddress.IPv4Address(bytes(packed[offset] for offset in _SIXTOFOUR_OFFSETS)))

    if address in _TEREDO_NETWORK:
        # RFC 4380: the client IPv4 sits in the low 32 bits, obfuscated by XOR with all-ones.
        candidates.append(ipaddress.IPv4Address(bytes(byte ^ 0xFF for byte in packed[12:16])))

    return candidates


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


async def _ensure_public_host(
    parsed_url: ParseResult, dns_resolver: DnsResolver | None, allow_private_network_access: bool = False
) -> None:
    host = parsed_url.hostname
    if host is None:
        raise FunctionExecutionException(f"The request URI '{parsed_url.geturl()}' does not contain a valid host.")

    try:
        ip_address = ipaddress.ip_address(host)
    except ValueError:
        addresses = await _resolve_host(host, dns_resolver)
    else:
        _ensure_public_address(parsed_url.geturl(), ip_address, allow_private_network_access)
        return

    if not addresses:
        raise FunctionExecutionException(
            f"The request URI '{parsed_url.geturl()}' is not allowed: DNS resolution for host "
            f"'{host}' returned no addresses. The request is blocked as a precaution."
        )

    for address in addresses:
        _ensure_public_address(parsed_url.geturl(), address, allow_private_network_access)


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
    url: str, address: ipaddress.IPv4Address | ipaddress.IPv6Address, allow_private_network_access: bool = False
) -> None:
    if is_cloud_metadata_address(address):
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed: host resolves to a cloud metadata endpoint ({address}), "
            "which is blocked to prevent Server-Side Request Forgery (SSRF). To allow this URL, add it to "
            "server_url_validation_allowed_base_urls."
        )
    if allow_private_network_access:
        return

    blocked, category = try_categorize_non_public_address(address)
    if blocked:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed: host resolves to a {category} address ({address}), "
            "which is blocked by default to prevent Server-Side Request Forgery (SSRF). "
            "To allow this URL, add it to server_url_validation_allowed_base_urls or set "
            "allow_private_network_access=True."
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
    if address in _NAT64_LOCAL_USE_NETWORK:
        return True, "NAT64 local-use prefix"

    return False, ""
