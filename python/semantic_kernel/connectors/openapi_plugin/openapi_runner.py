# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from inspect import isawaitable
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
from openapi_core import Spec

from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_run_options import RestApiRunOptions
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class OpenApiRunner:
    """The OpenApiRunner that runs the operations defined in the OpenAPI manifest."""

    payload_argument_name = "payload"
    media_type_application_json = "application/json"

    def __init__(
        self,
        parsed_openapi_document: Mapping[str, str],
        auth_callback: Callable[..., dict[str, str] | Awaitable[dict[str, str]]] | None = None,
        http_client: httpx.AsyncClient | None = None,
        enable_dynamic_payload: bool = True,
        enable_payload_namespacing: bool = False,
    ):
        """Initialize the OpenApiRunner."""
        self.spec = Spec.from_dict(parsed_openapi_document)  # type: ignore
        self.auth_callback = auth_callback
        self.http_client = http_client
        self.enable_dynamic_payload = enable_dynamic_payload
        self.enable_payload_namespacing = enable_payload_namespacing

    def build_full_url(self, base_url, query_string):
        """Build the full URL."""
        url_parts = list(urlparse(base_url))
        url_parts[4] = query_string
        return urlunparse(url_parts)

    def build_operation_url(
        self, operation: RestApiOperation, arguments: KernelArguments, server_url_override=None, api_host_url=None
    ):
        """Build the operation URL."""
        url = operation.build_operation_url(arguments, server_url_override, api_host_url)
        return self.build_full_url(url, operation.build_query_string(arguments))

    def build_json_payload(self, payload_metadata: RestApiPayload, arguments: dict[str, Any]) -> tuple[str, str]:
        """Build the JSON payload."""
        if self.enable_dynamic_payload:
            if payload_metadata is None:
                raise FunctionExecutionException(
                    "Payload can't be built dynamically due to the missing payload metadata."
                )

            payload = self.build_json_object(payload_metadata.properties, arguments)
            content = json.dumps(payload)
            return content, payload_metadata.media_type

        argument = arguments.get(self.payload_argument_name)
        if not isinstance(argument, str):
            raise FunctionExecutionException(f"No payload is provided by the argument '{self.payload_argument_name}'.")

        return argument, argument

    def build_json_object(self, properties, arguments, property_namespace=None):
        """Build the JSON payload object."""
        result = {}

        for property_metadata in properties:
            argument_name = self.get_argument_name_for_payload(property_metadata.name, property_namespace)
            if property_metadata.type == "object":
                node = self.build_json_object(property_metadata.properties, arguments, argument_name)
                result[property_metadata.name] = node
                continue
            property_value = arguments.get(argument_name)
            if property_value is not None:
                result[property_metadata.name] = property_value
                continue
            if property_metadata.is_required:
                raise FunctionExecutionException(
                    f"No argument is found for the '{property_metadata.name}' payload property."
                )
        return result

    def build_operation_payload(
        self, operation: RestApiOperation, arguments: KernelArguments
    ) -> tuple[str, str] | tuple[None, None]:
        """Build the operation payload."""
        if operation.request_body is None and self.payload_argument_name not in arguments:
            return None, None

        if operation.request_body is not None:
            return self.build_json_payload(operation.request_body, arguments)

        return None, None

    def get_argument_name_for_payload(self, property_name, property_namespace=None):
        """Get argument name for the payload."""
        if not self.enable_payload_namespacing:
            return property_name
        return f"{property_namespace}.{property_name}" if property_namespace else property_name

    def _get_first_response_media_type(self, responses: OrderedDict[str, RestApiExpectedResponse] | None) -> str:
        if responses:
            first_response = next(iter(responses.values()))
            return first_response.media_type if first_response.media_type else self.media_type_application_json
        return self.media_type_application_json

    async def run_operation(
        self,
        operation: RestApiOperation,
        arguments: KernelArguments | None = None,
        options: RestApiRunOptions | None = None,
    ) -> str:
        """Runs the operation defined in the OpenAPI manifest."""
        if not arguments:
            arguments = KernelArguments()
        url = self.build_operation_url(
            operation=operation,
            arguments=arguments,
            server_url_override=options.server_url_override if options else None,
            api_host_url=options.api_host_url if options else None,
        )
        headers = operation.build_headers(arguments=arguments)
        payload, _ = self.build_operation_payload(operation=operation, arguments=arguments)

        if self.auth_callback:
            headers_update = self.auth_callback(**headers)
            if isawaitable(headers_update):
                headers_update = await headers_update
            # at this point, headers_update is a valid dictionary
            headers.update(headers_update)  # type: ignore

        if APP_INFO:
            headers.update(APP_INFO)
            headers = prepend_semantic_kernel_to_user_agent(headers)

        if "Content-Type" not in headers:
            responses = (
                operation.responses
                if isinstance(operation.responses, OrderedDict)
                else OrderedDict(operation.responses or {})
            )
            headers["Content-Type"] = self._get_first_response_media_type(responses)

        async def fetch():
            async def make_request(client: httpx.AsyncClient):
                merged_headers = client.headers.copy()
                merged_headers.update(headers)
                response = await client.request(
                    method=operation.method,
                    url=url,
                    headers=merged_headers,
                    json=json.loads(payload) if payload else None,
                )
                response.raise_for_status()
                return response.text

            if hasattr(self, "http_client") and self.http_client is not None:
                return await make_request(self.http_client)
            async with httpx.AsyncClient(timeout=5) as client:
                return await make_request(client)

        return await fetch()
