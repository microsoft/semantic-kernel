import json
import logging
import sys
from typing import Dict, Mapping, Optional, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from urllib.parse import urljoin

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

    def validate_request(self, spec: Spec, **kwargs):
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
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
        summary: Optional[str] = None,
        description: Optional[str] = None,
        params: Optional[Mapping[str, str]] = None,
        request_body: Optional[Mapping[str, str]] = None,
    ):
        self.id = id
        self.method = method
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

    def prepare_request(
        self, path_params=None, query_params=None, headers=None, request_body=None
    ) -> PreparedRestApiRequest:
        path = self.path
        if path_params:
            path = path.format(**path_params)

        url = urljoin(self.server_url, path)

        processed_query_params, processed_headers = {}, headers
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
                    raise ValueError(f"Required path parameter {param_name} not provided")
                    raise ServiceInvalidRequestError(f"Required path parameter {param_name} not provided")

        processed_payload = None
        if self.request_body:
            if request_body is None and "required" in self.request_body and self.request_body["required"]:
                raise ValueError("Payload is required but was not provided")
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
    def __init__(self, **kwargs):
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")

    """
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

    def create_rest_api_operations(self, parsed_document) -> Dict[str, RestApiOperation]:
        paths = parsed_document.get("paths", {})
        request_objects = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                server_url = parsed_document.get("servers", [])
                server_url = server_url[0].get("url") if server_url else "/"

                request_method = method.lower()

                parameters = details.get("parameters", [])
                operationId = details.get("operationId", path + "_" + request_method)
                summary = details.get("summary", None)
                description = details.get("description", None)

                rest_api_operation = RestApiOperation(
                    id=operationId,
                    method=request_method,
                    server_url=server_url,
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
    ):
        self.spec = Spec.from_dict(parsed_openapi_document)

    async def run_operation(
        self,
        operation: RestApiOperation,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Union[str, Dict[str, str]]] = None,
    ) -> str:
        prepared_request = operation.prepare_request(
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            request_body=request_body,
        )
        is_valid = prepared_request.validate_request(spec=self.spec)
        if not is_valid:
            return None

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
Registers a plugin with the kernel that can run OpenAPI operations.
:param kernel: The kernel to register the plugin with
:param plugin_name: The name of the plugin
:param openapi_document: The OpenAPI document to register. Can be a filename or URL
:return: A dictionary of KernelFunctions keyed by operationId
"""


def register_openapi_plugin(
    kernel: Kernel,
    plugin_name: str,
    openapi_document: str,
) -> Dict[str, KernelFunction]:
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    operations = parser.create_rest_api_operations(parsed_doc)
    openapi_runner = OpenApiRunner(parsed_openapi_document=parsed_doc)

    plugin = {}

    def create_run_operation_function(runner: OpenApiRunner, operation: RestApiOperation):
        @kernel_function(
            description=operation.summary if operation.summary else operation.description,
            name=operation_id,
        )
        async def run_openapi_operation(
            path_params: Annotated[Optional[Union[Dict, str]], "A dictionary of path parameters"] = None,
            query_params: Annotated[Optional[Union[Dict, str]], "A dictionary of query parameters"] = None,
            headers: Annotated[Optional[Union[Dict, str]], "A dictionary of headers"] = None,
            request_body: Annotated[Optional[Union[Dict, str]], "A dictionary of the request body"] = None,
        ) -> str:
            response = await runner.run_operation(
                operation,
                path_params=json.loads(path_params)
                if isinstance(path_params, str)
                else path_params
                if path_params
                else None,
                query_params=json.loads(query_params)
                if isinstance(query_params, str)
                else query_params
                if query_params
                else None,
                headers=json.loads(headers) if isinstance(headers, str) else headers if headers else None,
                request_body=json.loads(request_body)
                if isinstance(request_body, str)
                else request_body
                if request_body
                else None,
            )
            return response

        return run_openapi_operation

    for operation_id, operation in operations.items():
        logger.info(f"Registering OpenAPI operation: {plugin_name}.{operation_id}")
        plugin[operation_id] = create_run_operation_function(openapi_runner, operation)
    return kernel.import_plugin(plugin, plugin_name)
    return kernel.import_plugin_from_object(plugin, plugin_name)
