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
        kernel.add_plugin(HttpPlugin(), "http")

        # With allowed domains for security:
        kernel.add_plugin(HttpPlugin(allowed_domains=["example.com", "api.example.com"]), "http")

    Examples:
        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}
    """

    allowed_domains: set[str] | None = None
    """List of allowed domains to send requests to. If None, all domains are allowed."""

    def _is_uri_allowed(self, url: str) -> bool:
        """Check if the URL's host is in the allowed domains list.

        Args:
            url: The URL to check.

        Returns:
            True if the URL is allowed, False otherwise.
        """
        if self.allowed_domains is None:
            return True

        parsed = urlparse(url)
        host = parsed.hostname
        if host is None:
            return False

        # Case-insensitive comparison
        return host.lower() in {domain.lower() for domain in self.allowed_domains}

    def _validate_url(self, url: str) -> None:
        """Validate the URL, checking if it's not empty and is in the allowed domains.

        Args:
            url: The URL to validate.

        Raises:
            FunctionExecutionException: If the URL is empty or not in the allowed domains.
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

        async with aiohttp.ClientSession() as session, session.get(url, raise_for_status=True) as response:
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
            session.post(url, headers=headers, data=data, raise_for_status=True) as response,
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
            session.put(url, headers=headers, data=data, raise_for_status=True) as response,
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

        async with aiohttp.ClientSession() as session, session.delete(url, raise_for_status=True) as response:
            return await response.text()
