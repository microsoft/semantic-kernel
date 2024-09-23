# Copyright (c) Microsoft. All rights reserved.

import json
<<<<<<< main
from typing import Annotated, Any

import aiohttp

from semantic_kernel.exceptions import FunctionExecutionException
=======
import sys
from typing import Any, Dict, Optional

import aiohttp

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

>>>>>>> ms/small_fixes
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class HttpPlugin(KernelBaseModel):
    """A plugin that provides HTTP functionality.

    Usage:
        kernel.add_plugin(HttpPlugin(), "http")

    Examples:
        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}
    """

<<<<<<< main
    @kernel_function(description="Makes a GET request to a url", name="getAsync")
    async def get(self, url: Annotated[str, "The URL to send the request to."]) -> str:
        """Sends an HTTP GET request to the specified URI and returns the response body as a string.

        Args:
            url: The URL to send the request to.

        Returns:
=======
    @kernel_function(description="Makes a GET request to a uri", name="getAsync")
    async def get(self, url: Annotated[str, "The URI to send the request to."]) -> str:
        """
        Sends an HTTP GET request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
>>>>>>> ms/small_fixes
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, raise_for_status=True) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a POST request to a uri", name="postAsync")
    async def post(
        self,
        url: Annotated[str, "The URI to send the request to."],
<<<<<<< main
        body: Annotated[dict[str, Any] | None, "The body of the request"] = {},
    ) -> str:
        """Sends an HTTP POST request to the specified URI and returns the response body as a string.

        Args:
=======
        body: Annotated[Optional[Dict[str, Any]], "The body of the request"] = {},
    ) -> str:
        """
        Sends an HTTP POST request to the specified URI and returns
        the response body as a string.
        params:
>>>>>>> ms/small_fixes
            url: The URI to send the request to.
            body: Contains the body of the request
        returns:
            The response body as a string.
        """
        if not url:
<<<<<<< main
            raise FunctionExecutionException("url cannot be `None` or empty")
=======
            raise ValueError("url cannot be `None` or empty")
>>>>>>> ms/small_fixes

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url, headers=headers, data=data, raise_for_status=True
            ) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a PUT request to a uri", name="putAsync")
    async def put(
        self,
        url: Annotated[str, "The URI to send the request to."],
<<<<<<< main
        body: Annotated[dict[str, Any] | None, "The body of the request"] = {},
    ) -> str:
        """Sends an HTTP PUT request to the specified URI and returns the response body as a string.

        Args:
=======
        body: Annotated[Optional[Dict[str, Any]], "The body of the request"] = {},
    ) -> str:
        """
        Sends an HTTP PUT request to the specified URI and returns
        the response body as a string.
        params:
>>>>>>> ms/small_fixes
            url: The URI to send the request to.
            body: Contains the body of the request

        Returns:
            The response body as a string.
        """
        if not url:
<<<<<<< main
            raise FunctionExecutionException("url cannot be `None` or empty")
=======
            raise ValueError("url cannot be `None` or empty")
>>>>>>> ms/small_fixes

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with (
            aiohttp.ClientSession() as session,
            session.put(
                url, headers=headers, data=data, raise_for_status=True
            ) as response,
        ):
            return await response.text()

    @kernel_function(description="Makes a DELETE request to a uri", name="deleteAsync")
<<<<<<< main
    async def delete(
        self, url: Annotated[str, "The URI to send the request to."]
    ) -> str:
        """Sends an HTTP DELETE request to the specified URI and returns the response body as a string.

        Args:
            url: The URI to send the request to.

        Returns:
=======
    async def delete(self, url: Annotated[str, "The URI to send the request to."]) -> str:
        """
        Sends an HTTP DELETE request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
>>>>>>> ms/small_fixes
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")
        async with (
            aiohttp.ClientSession() as session,
            session.delete(url, raise_for_status=True) as response,
        ):
            return await response.text()
