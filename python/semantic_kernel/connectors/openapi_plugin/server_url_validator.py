# Copyright (c) Microsoft. All rights reserved.

import ipaddress
from typing import Any
from urllib.parse import ParseResult, urlparse

from pydantic import Field

from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.public_network_address_validator import DnsResolver, ensure_public_host

DEFAULT_ALLOWED_SCHEME = "https"


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
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Validate a fully resolved OpenAPI operation URL against the supplied policy.

    Returns the DNS-resolved addresses that were vetted by this call, in resolver order,
    so that the caller can pin the connection to an address the policy actually approved
    (closing the DNS check-time/use-time gap known as DNS rebinding).

    The list is empty whenever there is nothing to pin, and callers must then connect
    normally: when an allowed base URL matched, when ``allow_private_network_access``
    is set, or when the host is already a literal IP address (which cannot be rebound).
    """
    options = options or ServerUrlValidationOptions()
    try:
        parsed_url = _parse_absolute_url(url)
    except ValueError as exc:
        raise FunctionExecutionException(
            f"The request URI '{url}' is not allowed because it is not a valid absolute URI."
        ) from exc

    if _matches_allowed_base_url(parsed_url, options.allowed_base_urls):
        return []

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
        return []

    return await ensure_public_host(
        parsed_url,
        dns_resolver,
        configuration_hint=(
            "To allow this URL, add it to server_url_validation_allowed_base_urls or set "
            "allow_private_network_access=True."
        ),
    )


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
