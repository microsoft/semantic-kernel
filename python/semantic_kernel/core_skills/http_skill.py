# Copyright (c) Microsoft. All rights reserved.

import json
import typing as t

import aiohttp

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class HttpSkill(PydanticField):
    """
    A skill that provides HTTP functionality.

    Usage:
        kernel.import_skill(HttpSkill(), "http")

    Examples:

        {{http.getAsync $url}}
        {{http.postAsync $url}}
        {{http.putAsync $url}}
        {{http.deleteAsync $url}}
    """

    @sk_function(description="Makes a GET request to a uri", name="getAsync")
    async def get_async(self, url: str) -> str:
        """
        Sends an HTTP GET request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise ValueError("url cannot be `None` or empty")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, raise_for_status=True) as response:
                return await response.text()

    @sk_function(description="Makes a POST request to a uri", name="postAsync")
    @sk_function_context_parameter(name="body", description="The body of the request")
    async def post_async(self, url: str, context: "SKContext") -> str:
        """
        Sends an HTTP POST request to the specified URI and returns
        the response body as a string.
        params:
            url: The URI to send the request to.
            context: Contains the body of the request
        returns:
            The response body as a string.
        """
        if not url:
            raise ValueError("url cannot be `None` or empty")

        _, body = context.variables.get("body")

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, data=data, raise_for_status=True
            ) as response:
                return await response.text()

    @sk_function(description="Makes a PUT request to a uri", name="putAsync")
    @sk_function_context_parameter(name="body", description="The body of the request")
    async def put_async(self, url: str, context: "SKContext") -> str:
        """
        Sends an HTTP PUT request to the specified URI and returns
        the response body as a string.
        params:
            url: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise ValueError("url cannot be `None` or empty")

        _, body = context.variables.get("body")

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url, headers=headers, data=data, raise_for_status=True
            ) as response:
                return await response.text()

    @sk_function(description="Makes a DELETE request to a uri", name="deleteAsync")
    async def delete_async(self, url: str) -> str:
        """
        Sends an HTTP DELETE request to the specified URI and returns
        the response body as a string.
        params:
            uri: The URI to send the request to.
        returns:
            The response body as a string.
        """
        if not url:
            raise ValueError("url cannot be `None` or empty")
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, raise_for_status=True) as response:
                return await response.text()
