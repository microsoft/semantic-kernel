# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from typing import Any, Dict, Optional

import aiohttp

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class HttpPlugin(KernelBaseModel):
    """
    A plugin that provides HTTP functionality.

    Usage:
        kernel.import_plugin_from_object(HttpPlugin(), "http")

    Examples:

        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}
    """

    @kernel_function(description="Makes a GET request to a uri", name="getAsync")
    async def get(self, url: Annotated[str, "The URI to send the request to."]) -> str:
        """
        Sends an HTTP GET request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, raise_for_status=True) as response:
                return await response.text()

    @kernel_function(description="Makes a POST request to a uri", name="postAsync")
    async def post(
        self,
        url: Annotated[str, "The URI to send the request to."],
        body: Annotated[Optional[Dict[str, Any]], "The body of the request"] = {},
    ) -> str:
        """
        Sends an HTTP POST request to the specified URI and returns
        the response body as a string.
        params:
            url: The URI to send the request to.
            body: Contains the body of the request
        returns:
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data, raise_for_status=True) as response:
                return await response.text()

    @kernel_function(description="Makes a PUT request to a uri", name="putAsync")
    async def put(
        self,
        url: Annotated[str, "The URI to send the request to."],
        body: Annotated[Optional[Dict[str, Any]], "The body of the request"] = {},
    ) -> str:
        """
        Sends an HTTP PUT request to the specified URI and returns
        the response body as a string.
        params:
            url: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, data=data, raise_for_status=True) as response:
                return await response.text()

    @kernel_function(description="Makes a DELETE request to a uri", name="deleteAsync")
    async def delete(self, url: Annotated[str, "The URI to send the request to."]) -> str:
        """
        Sends an HTTP DELETE request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise FunctionExecutionException("url cannot be `None` or empty")
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, raise_for_status=True) as response:
                return await response.text()
