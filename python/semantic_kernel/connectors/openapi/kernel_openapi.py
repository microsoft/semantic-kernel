# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import json
import logging
import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from urllib.parse import urljoin, urlparse, urlunparse

import aiohttp
import requests
from openapi_core import Spec, unmarshal_request
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.exceptions import OpenAPIError
from prance import ResolvingParser

from semantic_kernel.connectors.ai.open_ai.const import (
    USER_AGENT,
)
from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT
from semantic_kernel.exceptions import ServiceInvalidRequestError
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
        OpenAIFunctionExecutionParameters,
    )
    from semantic_kernel.connectors.openapi.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

logger: logging.Logger = logging.getLogger(__name__)


class PreparedRestApiRequest:
    def __init__(self, method: str, url: str, params=None, headers=None, request_body=None):
        self.method = method
        self.url = url
        self.params = params
        self.headers = headers
        self.request_body = request_body

    def __repr__(self):
        return (
            "PreparedRestApiRequest("
            f"method={self.method}, "
            f"url={self.url}, "
            f"params={self.params}, "
            f"headers={self.headers}, "
            f"request_body={self.request_body})"
        )

    def validate_request(self, spec: Spec):
        request = requests.Request(
            self.method,
            self.url,
            params=self.params,
            headers=self.headers,
            json=self.request_body,
        )
        openapi_request = RequestsOpenAPIRequest(request=request)
        try:
            unmarshal_request(openapi_request, spec=spec)
            return True
        except OpenAPIError as e:
            logger.debug(f"Error validating request: {e}", exc_info=True)
            return False


class RestApiOperation:
    def __init__(
        self,
        id: str,
        method: str,
        server_url: str,
        path: str,
        summary: str | None = None,
        description: str | None = None,
        params: Mapping[str, str] | None = None,
        request_body: Mapping[str, str] | None = None,
    ):
        self.id = id
        self.method = method.upper()
        self.server_url = server_url
        self.path = path
        self.summary = summary
        self.description = description
        self.params = params
        self.request_body = request_body

    """
    Fills in this RestApiOperation's parameters and payload with the provided values
    :param path_params: A dictionary of path parameters
    :param query_params: A dictionary of query parameters
    :param headers: A dictionary of headers
    :param request_body: The payload of the request
    :return: A PreparedRestApiRequest object
    """

    def url_join(self, base_url, path):
        """Join a base URL and a path, correcting for any missing slashes."""
        parsed_base = urlparse(base_url)
        if not parsed_base.path.endswith("/"):
            base_path = parsed_base.path + "/"
        else:
            base_path = parsed_base.path
        full_path = urljoin(base_path, path.lstrip("/"))
        return urlunparse(parsed_base._replace(path=full_path))

    def prepare_request(
        self, path_params=None, query_params=None, headers=None, request_body=None
    ) -> PreparedRestApiRequest:
        path = self.path
        if path_params:
            path = path.format(**path_params)

        url = self.url_join(self.server_url, path)

        processed_query_params = {}
        processed_headers = headers if headers is not None else {}
        for param in self.params:
            param_name = param["name"]
            param_schema = param["schema"]
            param_default = param_schema.get("default", None)

            if param["in"] == "query":
                if query_params and param_name in query_params:
                    processed_query_params[param_name] = query_params[param_name]
                elif param["schema"] and "default" in param["schema"] is not None:
                    processed_query_params[param_name] = param_default
            elif param["in"] == "header":
                if headers and param_name in headers:
                    processed_headers[param_name] = headers[param_name]
                elif param_default is not None:
                    processed_headers[param_name] = param_default
            elif param["in"] == "path":
                if not path_params or param_name not in path_params:
                    raise ServiceInvalidRequestError(f"Required path parameter {param_name} not provided")

        processed_payload = None
        if self.request_body and (self.method == "POST" or self.method == "PUT"):
            if request_body is None and "required" in self.request_body and self.request_body["required"]:
                raise ServiceInvalidRequestError("Payload is required but was not provided")
            content = self.request_body["content"]
            content_type = list(content.keys())[0]
            processed_headers["Content-Type"] = content_type
            processed_payload = request_body

        processed_headers[USER_AGENT] = " ".join((HTTP_USER_AGENT, processed_headers.get(USER_AGENT, ""))).rstrip()

        req = PreparedRestApiRequest(
            method=self.method,
            url=url,
            params=processed_query_params,
            headers=processed_headers,
            request_body=processed_payload,
        )
        return req

    def __repr__(self):
        return (
            "RestApiOperation("
            f"id={self.id}, "
            f"method={self.method}, "
            f"server_url={self.server_url}, "
            f"path={self.path}, "
            f"params={self.params}, "
            f"request_body={self.request_body}, "
            f"summary={self.summary}, "
            f"description={self.description})"
        )


class OpenApiParser:
    """
    NOTE: SK Python only supports the OpenAPI Spec >=3.0

    Import an OpenAPI file.
    :param openapi_file: The path to the OpenAPI file which can be local or a URL.
    :return: The parsed OpenAPI file
    """

    def parse(self, openapi_document):
        parser = ResolvingParser(openapi_document)
        return parser.specification

    """
    Creates a RestApiOperation object for each path/method combination
    :param parsed_document: The parsed OpenAPI document
    :return: A dictionary of RestApiOperation objects keyed by operationId
    """

    def create_rest_api_operations(
        self,
        parsed_document: Any,
        execution_settings: "OpenAIFunctionExecutionParameters" | "OpenAPIFunctionExecutionParameters" | None = None,
    ) -> Dict[str, RestApiOperation]:
        paths = parsed_document.get("paths", {})
        request_objects = {}

        base_url = "/"
        servers = parsed_document.get("servers", [])
        base_url = servers[0].get("url") if servers else "/"

        if execution_settings and execution_settings.server_url_override:
            base_url = execution_settings.server_url_override

        for path, methods in paths.items():
            for method, details in methods.items():
                request_method = method.lower()

                parameters = details.get("parameters", [])
                operationId = details.get("operationId", path + "_" + request_method)
                summary = details.get("summary", None)
                description = details.get("description", None)

                rest_api_operation = RestApiOperation(
                    id=operationId,
                    method=request_method,
                    server_url=base_url,
                    path=path,
                    params=parameters,
                    request_body=details.get("requestBody", None),
                    summary=summary,
                    description=description,
                )

                request_objects[operationId] = rest_api_operation
        return request_objects


class OpenApiRunner:
    def __init__(
        self,
        parsed_openapi_document: Mapping[str, str],
        auth_callback: Callable[[Dict[str, str]], Dict[str, str]] | None = None,
    ):
        self.spec = Spec.from_dict(parsed_openapi_document)
        self.auth_callback = auth_callback

    async def run_operation(
        self,
        operation: RestApiOperation,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None,
        headers: Dict[str, str] | None = None,
        request_body: str | Dict[str, str] | None = None,
    ) -> str:
        if headers is None:
            headers = {}

        if self.auth_callback:
            headers_update = await self.auth_callback(headers=headers)
            headers.update(headers_update)

        prepared_request = operation.prepare_request(
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            request_body=request_body,
        )
        # TODO - figure out how to validate a request that has a dynamic API
        # against a spec that has a template path

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.request(
                prepared_request.method,
                prepared_request.url,
                params=prepared_request.params,
                headers=prepared_request.headers,
                json=prepared_request.request_body,
            ) as response:
                return await response.text()


"""
Imports a plugin with the kernel that can run OpenAPI operations.
:param kernel: The kernel to register the plugin with
:param plugin_name: The name of the plugin
:param openapi_document: The OpenAPI document to register. Can be a filename or URL
:return: A dictionary of KernelFunctions keyed by operationId
"""


def import_plugin_from_openapi(
    kernel: Kernel,
    plugin_name: str,
    openapi_document: str,
    execution_settings: "OpenAIFunctionExecutionParameters" | "OpenAPIFunctionExecutionParameters" | None = None,
) -> Dict[str, KernelFunction]:
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=execution_settings)

    auth_callback = None
    if execution_settings and execution_settings.auth_callback:
        auth_callback = execution_settings.auth_callback
    openapi_runner = OpenApiRunner(parsed_openapi_document=parsed_doc, auth_callback=auth_callback)

    plugin = {}

    def create_run_operation_function(runner: OpenApiRunner, operation: RestApiOperation):
        @kernel_function(
            description=operation.summary if operation.summary else operation.description,
            name=operation_id,
        )
        async def run_openapi_operation(
            path_params: Annotated[dict | str | None, "A dictionary of path parameters"] = None,
            query_params: Annotated[dict | str | None, "A dictionary of query parameters"] = None,
            headers: Annotated[dict | str | None, "A dictionary of headers"] = None,
            request_body: Annotated[dict | str | None, "A dictionary of the request body"] = None,
        ) -> str:
            response = await runner.run_operation(
                operation,
                path_params=(
                    json.loads(path_params) if isinstance(path_params, str) else path_params if path_params else None
                ),
                query_params=(
                    json.loads(query_params)
                    if isinstance(query_params, str)
                    else query_params if query_params else None
                ),
                headers=json.loads(headers) if isinstance(headers, str) else headers if headers else None,
                request_body=(
                    json.loads(request_body)
                    if isinstance(request_body, str)
                    else request_body if request_body else None
                ),
            )
            return response

        return run_openapi_operation

    for operation_id, operation in operations.items():
        logger.info(f"Registering OpenAPI operation: {plugin_name}.{operation_id}")
        plugin[operation_id] = create_run_operation_function(openapi_runner, operation)
    return kernel.import_plugin_from_object(plugin, plugin_name)
