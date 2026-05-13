# Copyright (c) Microsoft. All rights reserved.

import json
from typing import Annotated, Any
from urllib.parse import urlparse

import aiohttp

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


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
          or ``allow_all_domains`` is set to True.
        - When ``allowed_domains`` is set and ``allow_all_domains`` is False, HTTP
          redirects are disabled to prevent redirect-based domain bypass (SSRF).
        - When ``allow_all_domains`` is True, redirects are allowed regardless of
          whether ``allowed_domains`` is also set.
        - Only ``http`` and ``https`` URL schemes are permitted.
    """

    allowed_domains: set[str] | None = None
    """Set of allowed domains to send requests to."""

    allow_all_domains: bool = False
    """When True, requests to any domain are allowed. Must be explicitly set."""

    _ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})

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

        # If allow_all_domains is set, skip domain check
        if self.allow_all_domains:
            return True

        # If allowed_domains is set, check against it
        if self.allowed_domains is not None:
            return host.lower() in {domain.lower() for domain in self.allowed_domains}

        # Default: deny all
        return False

    def _validate_url(self, url: str) -> None:
        """Validate the URL, checking scheme, emptiness, and allowed domains.

        Args:
            url: The URL to validate.

        Raises:
            FunctionExecutionException: If the URL is empty, uses a disallowed scheme,
                or targets a domain that is not allowed.
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
