# Copyright (c) Microsoft. All rights reserved.

import ipaddress
import json
import logging
import socket
from collections.abc import Sequence
from typing import Annotated, Any, ClassVar
from urllib.parse import urlparse

import aiohttp
from yarl import URL

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.public_network_address_validator import ensure_public_host

logger = logging.getLogger(__name__)

_NetworkAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class _ValidatedAddressResolver(aiohttp.abc.AbstractResolver):
    """Resolve one validated host only to addresses that were already vetted."""

    def __init__(self, host: str, addresses: Sequence[_NetworkAddress]) -> None:
        self._host = host
        self._addresses = addresses

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[Any]:
        """Return vetted addresses without performing another DNS lookup."""
        if host != self._host:
            raise OSError(f"Refusing to resolve host '{host}'; only '{self._host}' was validated.")

        results: list[Any] = []
        for address in self._addresses:
            address_family = socket.AF_INET6 if isinstance(address, ipaddress.IPv6Address) else socket.AF_INET
            if family not in (socket.AF_UNSPEC, address_family):
                continue
            results.append({
                "hostname": host,
                "host": str(address),
                "port": port,
                "family": address_family,
                "proto": socket.IPPROTO_TCP,
                "flags": socket.AI_NUMERICHOST,
            })
        return results

    async def close(self) -> None:
        """Release resolver resources."""


def _create_client_session(request_url: URL, validated_addresses: Sequence[_NetworkAddress]) -> aiohttp.ClientSession:
    if not validated_addresses:
        return aiohttp.ClientSession()

    host = request_url.raw_host
    if host is None:
        raise FunctionExecutionException("The request URL does not contain a valid host.")

    resolver = _ValidatedAddressResolver(host, validated_addresses)
    return aiohttp.ClientSession(connector=aiohttp.TCPConnector(resolver=resolver))


class HttpPlugin(KernelBaseModel):
    """A plugin that provides HTTP functionality.

    Usage:
        # With allowed domains (recommended):
        kernel.add_plugin(HttpPlugin(allowed_domains=["example.com", "api.example.com"]), "http")

        # Explicitly allow all domains (opt-in, less secure):
        kernel.add_plugin(HttpPlugin(allow_all_domains=True), "http")

    Examples:
        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}

    Security:
        - By default, all requests are blocked unless ``allowed_domains`` is provided
          or ``allow_all_domains`` is set to True. A warning is logged when neither
          option is configured.
        - When ``allowed_domains`` is set and ``allow_all_domains`` is False, HTTP
          redirects are disabled to prevent redirect-based domain bypass (SSRF).
        - When ``allow_all_domains`` is True, redirects are allowed regardless of
          whether ``allowed_domains`` is also set.
        - Only ``http`` and ``https`` URL schemes are permitted.
        - Only standard ports (80, 443) are permitted by default. Set ``allowed_ports``
          to permit additional ports. Port validation is skipped when
          ``allow_all_domains`` is True.
        - Allowed hosts are normalized using aiohttp's IDNA rules before DNS validation,
          and the same normalized URL is used for the request. Connections are pinned to
          the validated DNS addresses so the host cannot resolve to a different address
          when the connection is opened. Non-public addresses and DNS failures are blocked
          unless ``allow_private_network_access`` is True. ``allow_all_domains=True`` also
          bypasses this check.
    """

    allowed_domains: set[str] | None = None
    """Set of allowed domains to send requests to."""

    allow_all_domains: bool = False
    """Allow any domain, port, and network address, with redirects. Must be explicitly set."""

    allow_private_network_access: bool = False
    """Permit non-public addresses for allowed domains. Enable only for trusted internal endpoints.

    Domain and port restrictions still apply, and redirects remain disabled unless
    ``allow_all_domains`` is True.
    """

    allowed_ports: set[int] | None = None
    """Set of ports permitted for outbound requests. Defaults to ``{80, 443}`` when not set.

    Ignored when ``allow_all_domains`` is True. Set explicitly to permit non-standard ports
    (e.g. ``allowed_ports={443, 8443}``).
    """

    _ALLOWED_SCHEMES: ClassVar[frozenset[str]] = frozenset({"http", "https"})
    _DEFAULT_SCHEME_PORTS: ClassVar[dict[str, int]] = {"http": 80, "https": 443}
    _DEFAULT_ALLOWED_PORTS: ClassVar[frozenset[int]] = frozenset({80, 443})

    def model_post_init(self, __context: Any) -> None:
        """Warn when the default configuration blocks all requests."""
        super().model_post_init(__context)
        if self.allowed_domains is None and not self.allow_all_domains:
            logger.warning(
                "HttpPlugin was created without `allowed_domains` and with `allow_all_domains=False`; "
                "all HTTP requests will be blocked. Set `allowed_domains` or `allow_all_domains=True` "
                "to enable requests."
            )

    @property
    def _allow_redirects(self) -> bool:
        """Whether HTTP redirects should be followed.

        Redirects are only allowed when ``allow_all_domains`` is True.
        When domain restrictions are configured, redirects are disabled
        to prevent redirect-based SSRF bypass.
        """
        return self.allow_all_domains

    def _is_uri_allowed(self, url: str) -> bool:
        """Check if the URL's host and scheme are permitted.

        Args:
            url: The URL to check.

        Returns:
            True if the URL is allowed, False otherwise.
        """
        parsed = urlparse(url)

        # Validate scheme
        if parsed.scheme.lower() not in self._ALLOWED_SCHEMES:
            return False

        host = parsed.hostname
        if not host:
            return False

        # Validate that the port component is syntactically valid, regardless of
        # allow_all_domains. Accessing parsed.port raises ValueError for a malformed
        # or out-of-range port.
        try:
            port = parsed.port
        except ValueError:
            return False

        # If allow_all_domains is set, skip the domain and port allow-list checks.
        if self.allow_all_domains:
            return True

        # Enforce the port allow-list (deny-by-default to non-standard ports).
        if port is None:
            port = self._DEFAULT_SCHEME_PORTS.get(parsed.scheme.lower())
        allowed_ports = self.allowed_ports if self.allowed_ports is not None else self._DEFAULT_ALLOWED_PORTS
        if port not in allowed_ports:
            return False

        # If allowed_domains is set, check against it
        if self.allowed_domains is not None:
            return host.lower() in {domain.lower() for domain in self.allowed_domains}

        # Default: deny all
        return False

    async def _validate_url(self, url: str) -> tuple[URL, list[_NetworkAddress]]:
        """Validate and normalize the URL before sending a request.

        Always checks that the URL is non-empty, uses an allowed scheme, and has a
        syntactically valid port. When ``allow_all_domains`` is False, additionally
        enforces the port and domain allow-lists. Non-public addresses and DNS failures
        are rejected unless private-network access or unrestricted access is enabled.

        Args:
            url: The URL to validate.

        Returns:
            The normalized URL and any DNS addresses that must be pinned for the request.

        Raises:
            FunctionExecutionException: If the URL is empty, uses a disallowed scheme,
                has a malformed port, or (unless ``allow_all_domains`` is True) targets
                a port or domain that is not allowed, or resolves to a prohibited address.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        if not self._is_uri_allowed(url):
            raise FunctionExecutionException("Sending requests to the provided location is not allowed.")

        request_url = URL(url)
        validated_addresses: list[_NetworkAddress] = []
        if not self.allow_all_domains and not self.allow_private_network_access:
            validated_addresses = await ensure_public_host(
                urlparse(str(request_url)),
                configuration_hint="To allow trusted internal endpoints, set allow_private_network_access=True.",
            )

        return request_url, validated_addresses

    @kernel_function(description="Makes a GET request to a url", name="getAsync")
    async def get(self, url: Annotated[str, "The URL to send the request to."]) -> str:
        """Sends an HTTP GET request to the specified URI and returns the response body as a string.

        Args:
            url: The URL to send the request to.

        Returns:
            The response body as a string.
        """
        request_url, validated_addresses = await self._validate_url(url)

        async with (
            _create_client_session(request_url, validated_addresses) as session,
            session.get(request_url, raise_for_status=True, allow_redirects=self._allow_redirects) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a POST request to a uri", name="postAsync")
    async def post(
        self,
        url: Annotated[str, "The URI to send the request to."],
        body: Annotated[dict[str, Any] | None, "The body of the request"] = None,
    ) -> str:
        """Sends an HTTP POST request to the specified URI and returns the response body as a string.

        Args:
            url: The URI to send the request to.
            body: Contains the body of the request
        returns:
            The response body as a string.
        """
        request_url, validated_addresses = await self._validate_url(url)

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body) if body is not None else None
        async with (
            _create_client_session(request_url, validated_addresses) as session,
            session.post(
                request_url, headers=headers, data=data, raise_for_status=True, allow_redirects=self._allow_redirects
            ) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a PUT request to a uri", name="putAsync")
    async def put(
        self,
        url: Annotated[str, "The URI to send the request to."],
        body: Annotated[dict[str, Any] | None, "The body of the request"] = None,
    ) -> str:
        """Sends an HTTP PUT request to the specified URI and returns the response body as a string.

        Args:
            url: The URI to send the request to.
            body: Contains the body of the request

        Returns:
            The response body as a string.
        """
        request_url, validated_addresses = await self._validate_url(url)

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body) if body is not None else None
        async with (
            _create_client_session(request_url, validated_addresses) as session,
            session.put(
                request_url, headers=headers, data=data, raise_for_status=True, allow_redirects=self._allow_redirects
            ) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a DELETE request to a uri", name="deleteAsync")
    async def delete(self, url: Annotated[str, "The URI to send the request to."]) -> str:
        """Sends an HTTP DELETE request to the specified URI and returns the response body as a string.

        Args:
            url: The URI to send the request to.

        Returns:
            The response body as a string.
        """
        request_url, validated_addresses = await self._validate_url(url)

        async with (
            _create_client_session(request_url, validated_addresses) as session,
            session.delete(request_url, raise_for_status=True, allow_redirects=self._allow_redirects) as response,
        ):
            return await response.text()
