import json
import logging
from typing import Dict, Mapping, Optional, Union
from urllib.parse import urljoin

import aiohttp
import requests
from openapi_core import Spec, unmarshal_request
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.exceptions import OpenAPIError
from prance import ResolvingParser

from semantic_kernel import Kernel, SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel.utils.null_logger import NullLogger


class PreparedRestApiRequest:
    def __init__(
        self, method: str, url: str, params=None, headers=None, request_body=None
    ):
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

    def validate_request(self, spec: Spec, logger: logging.Logger = NullLogger()):
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

        processed_query_params, processed_headers = {}, {}
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
                    raise ValueError(
                        f"Required path parameter {param_name} not provided"
                    )

        processed_payload = None
        if self.request_body:
            if (
                request_body is None
                and "required" in self.request_body
                and self.request_body["required"]
            ):
                raise ValueError("Payload is required but was not provided")
            content = self.request_body["content"]
            content_type = list(content.keys())[0]
            processed_headers["Content-Type"] = content_type
            processed_payload = request_body

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
    def __init__(self, logger: logging.Logger = NullLogger()):
        self.logger = logger

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

    def create_rest_api_operations(
        self, parsed_document
    ) -> Dict[str, RestApiOperation]:
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
        logger: logging.Logger = NullLogger(),
    ):
        self.logger = logger
        self.spec = Spec.from_dict(parsed_openapi_document)

    async def run_operation(
        self,
        operation: RestApiOperation,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Union[str, Dict[str, str]]] = None,
    ) -> aiohttp.ClientResponse:
        prepared_request = operation.prepare_request(
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            request_body=request_body,
        )
        is_valid = prepared_request.validate_request(spec=self.spec, logger=self.logger)
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
Registers a skill with the kernel that can run OpenAPI operations.
:param kernel: The kernel to register the skill with
:param skill_name: The name of the skill
:param openapi_document: The OpenAPI document to register. Can be a filename or URL
:return: A dictionary of SKFunctions keyed by operationId
"""


def register_openapi_skill(
    kernel: Kernel,
    skill_name: str,
    openapi_document: str,
) -> Dict[str, SKFunctionBase]:
    parser = OpenApiParser(logger=kernel.logger)
    parsed_doc = parser.parse(openapi_document)
    operations = parser.create_rest_api_operations(parsed_doc)
    openapi_runner = OpenApiRunner(
        parsed_openapi_document=parsed_doc, logger=kernel.logger
    )

    skill = {}

    def create_run_operation_function(
        runner: OpenApiRunner, operation: RestApiOperation
    ):
        @sk_function(
            description=operation.summary
            if operation.summary
            else operation.description,
            name=operation_id,
        )
        @sk_function_context_parameter(
            name="path_params", description="A dictionary of path parameters"
        )
        @sk_function_context_parameter(
            name="query_params", description="A dictionary of query parameters"
        )
        @sk_function_context_parameter(
            name="headers", description="A dictionary of headers"
        )
        @sk_function_context_parameter(
            name="request_body", description="A dictionary of the request body"
        )
        async def run_openapi_operation(sk_context: SKContext) -> str:
            has_path_params, path_params = sk_context.variables.get("path_params")
            has_query_params, query_params = sk_context.variables.get("query_params")
            has_headers, headers = sk_context.variables.get("headers")
            has_request_body, request_body = sk_context.variables.get("request_body")

            response = await runner.run_operation(
                operation,
                path_params=json.loads(path_params) if has_path_params else None,
                query_params=json.loads(query_params) if has_query_params else None,
                headers=json.loads(headers) if has_headers else None,
                request_body=json.loads(request_body) if has_request_body else None,
            )
            return response

        return run_openapi_operation

    for operation_id, operation in operations.items():
        kernel.logger.info(
            f"Registering OpenAPI operation: {skill_name}.{operation_id}"
        )
        skill[operation_id] = create_run_operation_function(openapi_runner, operation)
    return kernel.import_skill(skill, skill_name)
