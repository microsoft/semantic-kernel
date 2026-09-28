# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Annotated, Any, ClassVar
from urllib.parse import urlparse

import aiohttp

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class HttpPlugin(KernelBaseModel):
    """A plugin that provides HTTP functionality.

    Usage:
        # Without domain restrictions (backward compatible, logs a warning):
        kernel.add_plugin(HttpPlugin(), "http")

        # With allowed domains (recommended):
        kernel.add_plugin(HttpPlugin(allowed_domains=["example.com", "api.example.com"]), "http")

        # Explicitly allow all domains, even when allowed_domains is also set:
        kernel.add_plugin(HttpPlugin(allow_all_domains=True), "http")

    Examples:
        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}

    Security:
        - When ``allowed_domains`` is not provided, requests to any HTTP or HTTPS
          domain are allowed for backward compatibility and a warning is logged.
        - When ``allowed_domains`` is set and ``allow_all_domains`` is False, HTTP
          redirects are disabled to prevent redirect-based domain bypass.
        - When ``allow_all_domains`` is True, redirects are allowed regardless of
          whether ``allowed_domains`` is also set.
        - Only ``http`` and ``https`` URL schemes are permitted.
        - When domain restrictions are configured, only standard ports (80, 443)
          are permitted by default. Set ``allowed_ports`` to permit additional ports.
    """

    allowed_domains: set[str] | None = None
    """Set of allowed domains to send requests to. If None, all domains are allowed."""

    allow_all_domains: bool = False
    """When True, requests to any domain are allowed, overriding ``allowed_domains``."""

    allowed_ports: set[int] | None = None
    """Set of ports permitted for outbound requests when domain restrictions are configured.

    Defaults to ``{80, 443}`` when not set. Set explicitly to permit non-standard
    ports (e.g. ``allowed_ports={443, 8443}``).
    """

    _ALLOWED_SCHEMES: ClassVar[frozenset[str]] = frozenset({"http", "https"})
    _DEFAULT_SCHEME_PORTS: ClassVar[dict[str, int]] = {"http": 80, "https": 443}
    _DEFAULT_ALLOWED_PORTS: ClassVar[frozenset[int]] = frozenset({80, 443})

    def model_post_init(self, __context: Any) -> None:
        """Warn when the plugin is configured without domain restrictions."""
        super().model_post_init(__context)
        if self.allowed_domains is None and not self.allow_all_domains:
            logger.warning(
                "HttpPlugin was created without `allowed_domains`; requests to any HTTP or HTTPS domain are allowed. "
                "Set `allowed_domains` to restrict outbound requests."
            )

    @property
    def _allow_redirects(self) -> bool:
        """Whether HTTP redirects should be followed.

        Redirects are allowed when domain restrictions are not configured or
        ``allow_all_domains`` is True.
        """
        return self.allow_all_domains or self.allowed_domains is None

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

        # Preserve unrestricted behavior when no domain allow-list is configured.
        if self.allow_all_domains or self.allowed_domains is None:
            return True

        # Enforce the port allow-list (deny-by-default to non-standard ports).
        if port is None:
            port = self._DEFAULT_SCHEME_PORTS.get(parsed.scheme.lower())
        allowed_ports = self.allowed_ports if self.allowed_ports is not None else self._DEFAULT_ALLOWED_PORTS
        if port not in allowed_ports:
            return False

        return host.lower() in {domain.lower() for domain in self.allowed_domains}

    def _validate_url(self, url: str) -> None:
        """Validate the URL before sending a request.

        Always checks that the URL is non-empty, uses an allowed scheme, and has a
        syntactically valid port. When domain restrictions are configured,
        additionally enforces the port and domain allow-lists.

        Args:
            url: The URL to validate.

        Raises:
            FunctionExecutionException: If the URL is empty, uses a disallowed scheme,
                has a malformed port, or targets a configured port or domain that is
                not allowed.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        if not self._is_uri_allowed(url):
            raise FunctionExecutionException("Sending requests to the provided location is not allowed.")

    @kernel_function(description="Makes a GET request to a url", name="getAsync")
    async def get(self, url: Annotated[str, "The URL to send the request to."]) -> str:
        """Sends an HTTP GET request to the specified URI and returns the response body as a string.

        Args:
            url: The URL to send the request to.

        Returns:
            The response body as a string.
        """
        self._validate_url(url)

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, raise_for_status=True, allow_redirects=self._allow_redirects) as response,
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
        self._validate_url(url)

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body) if body is not None else None
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url, headers=headers, data=data, raise_for_status=True, allow_redirects=self._allow_redirects
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
        self._validate_url(url)

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body) if body is not None else None
        async with (
            aiohttp.ClientSession() as session,
            session.put(
                url, headers=headers, data=data, raise_for_status=True, allow_redirects=self._allow_redirects
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
        self._validate_url(url)

        async with (
            aiohttp.ClientSession() as session,
            session.delete(url, raise_for_status=True, allow_redirects=self._allow_redirects) as response,
        ):
            return await response.text()
