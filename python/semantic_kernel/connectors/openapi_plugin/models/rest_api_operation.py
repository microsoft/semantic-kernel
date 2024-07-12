# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Any, Final
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_expected_response import (
    RestApiOperationExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter import RestApiOperationParameter
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter_location import (
    RestApiOperationParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter_style import (
    RestApiOperationParameterStyle,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_payload import RestApiOperationPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_payload_property import (
    RestApiOperationPayloadProperty,
)
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperation:
    MEDIA_TYPE_TEXT_PLAIN = "text/plain"
    PAYLOAD_ARGUMENT_NAME = "payload"
    CONTENT_TYPE_ARGUMENT_NAME = "content-type"
    INVALID_SYMBOLS_REGEX = re.compile(r"[^0-9A-Za-z_]+")

    _preferred_responses: Final[list[str]] = [
        "200",
        "201",
        "202",
        "203",
        "204",
        "205",
        "206",
        "207",
        "208",
        "226",
        "2XX",
        "default",
    ]

    def __init__(
        self,
        id: str,
        method: str,
        server_url: str,
        path: str,
        summary: str | None = None,
        description: str | None = None,
        params: list["RestApiOperationParameter"] | None = None,
        request_body: "RestApiOperationPayload | None" = None,
        responses: dict[str, "RestApiOperationExpectedResponse"] | None = None,
    ):
        """Initialize the RestApiOperation."""
        self.id = id
        self.method = method.upper()
        self.server_url = server_url
        self.path = path
        self.summary = summary
        self.description = description
        self.parameters = params
        self.request_body = request_body
        self.responses = responses

    def url_join(self, base_url: str, path: str):
        """Join a base URL and a path, correcting for any missing slashes."""
        parsed_base = urlparse(base_url)
        base_path = parsed_base.path + "/" if not parsed_base.path.endswith("/") else parsed_base.path
        full_path = urljoin(base_path, path.lstrip("/"))
        return urlunparse(parsed_base._replace(path=full_path))

    def build_headers(self, arguments: dict[str, Any]) -> dict[str, str]:
        """Build the headers for the operation."""
        headers = {}

        parameters = [p for p in self.parameters if p.location == RestApiOperationParameterLocation.HEADER]

        for parameter in parameters:
            argument = arguments.get(parameter.name)

            if argument is None:
                if parameter.is_required:
                    raise FunctionExecutionException(
                        f"No argument is provided for the `{parameter.name}` "
                        f"required parameter of the operation - `{self.id}`."
                    )
                continue

            headers[parameter.name] = str(argument)

        return headers

    def build_operation_url(self, arguments, server_url_override=None, api_host_url=None):
        """Build the URL for the operation."""
        server_url = self.get_server_url(server_url_override, api_host_url)
        path = self.build_path(self.path, arguments)
        return urljoin(server_url.geturl(), path.lstrip("/"))

    def get_server_url(self, server_url_override=None, api_host_url=None):
        """Get the server URL for the operation."""
        if server_url_override is not None and server_url_override.geturl() != b"":
            server_url_string = server_url_override.geturl()
        else:
            server_url_string = (
                self.server_url.geturl()
                if self.server_url
                else api_host_url.geturl()
                if api_host_url
                else self._raise_invalid_operation_exception()
            )

        # make sure the base URL ends with a trailing slash
        if not server_url_string.endswith("/"):
            server_url_string += "/"

        return urlparse(server_url_string)

    def build_path(self, path_template: str, arguments: dict[str, Any]) -> str:
        """Build the path for the operation."""
        parameters = [p for p in self.parameters if p.location == RestApiOperationParameterLocation.PATH]
        for parameter in parameters:
            argument = arguments.get(parameter.name)
            if argument is None:
                if parameter.is_required:
                    raise FunctionExecutionException(
                        f"No argument is provided for the `{parameter.name}` "
                        f"required parameter of the operation - `{self.id}`."
                    )
                continue
            path_template = path_template.replace(f"{{{parameter.name}}}", str(argument))
        return path_template

    def build_query_string(self, arguments: dict[str, Any]) -> str:
        """Build the query string for the operation."""
        segments = []
        parameters = [p for p in self.parameters if p.location == RestApiOperationParameterLocation.QUERY]
        for parameter in parameters:
            argument = arguments.get(parameter.name)
            if argument is None:
                if parameter.is_required:
                    raise FunctionExecutionException(
                        f"No argument or value is provided for the `{parameter.name}` "
                        f"required parameter of the operation - `{self.id}`."
                    )
                continue
            segments.append((parameter.name, argument))
        return urlencode(segments)

    def replace_invalid_symbols(self, parameter_name):
        """Replace invalid symbols in the parameter name with underscores."""
        return RestApiOperation.INVALID_SYMBOLS_REGEX.sub("_", parameter_name)

    def get_parameters(
        self,
        operation: "RestApiOperation",
        add_payload_params_from_metadata: bool = True,
        enable_payload_spacing: bool = False,
    ) -> list["RestApiOperationParameter"]:
        """Get the parameters for the operation."""
        params = list(operation.parameters)
        if operation.request_body is not None:
            params.extend(
                self.get_payload_parameters(
                    operation=operation,
                    use_parameters_from_metadata=add_payload_params_from_metadata,
                    enable_namespacing=enable_payload_spacing,
                )
            )

        for parameter in params:
            parameter.alternative_name = self.replace_invalid_symbols(parameter.name)

        return params

    def create_payload_artificial_parameter(self, operation: "RestApiOperation") -> "RestApiOperationParameter":
        """Create an artificial parameter for the REST API request body."""
        return RestApiOperationParameter(
            name=self.PAYLOAD_ARGUMENT_NAME,
            type=(
                "string"
                if operation.request_body
                and operation.request_body.media_type == RestApiOperation.MEDIA_TYPE_TEXT_PLAIN
                else "object"
            ),
            is_required=True,
            location=RestApiOperationParameterLocation.BODY,
            style=RestApiOperationParameterStyle.SIMPLE,
            description=operation.request_body.description if operation.request_body else "REST API request body.",
            schema=operation.request_body.schema if operation.request_body else None,
        )

    def create_content_type_artificial_parameter(self) -> "RestApiOperationParameter":
        """Create an artificial parameter for the content type of the REST API request body."""
        return RestApiOperationParameter(
            name=self.CONTENT_TYPE_ARGUMENT_NAME,
            type="string",
            is_required=False,
            location=RestApiOperationParameterLocation.BODY,
            style=RestApiOperationParameterStyle.SIMPLE,
            description="Content type of REST API request body.",
        )

    def _get_property_name(
        self, property: RestApiOperationPayloadProperty, root_property_name: bool, enable_namespacing: bool
    ):
        if enable_namespacing and root_property_name:
            return f"{root_property_name}.{property.name}"
        return property.name

    def _get_parameters_from_payload_metadata(
        self,
        properties: list["RestApiOperationPayloadProperty"],
        enable_namespacing: bool = False,
        root_property_name: bool | None = None,
    ) -> list["RestApiOperationParameter"]:
        parameters: list[RestApiOperationParameter] = []
        for property in properties:
            parameter_name = self._get_property_name(property, root_property_name, enable_namespacing)
            if not property.properties:
                parameters.append(
                    RestApiOperationParameter(
                        name=parameter_name,
                        type=property.type,
                        is_required=property.is_required,
                        location=RestApiOperationParameterLocation.BODY,
                        style=RestApiOperationParameterStyle.SIMPLE,
                        description=property.description,
                        schema=property.schema,
                    )
                )
            parameters.extend(
                self._get_parameters_from_payload_metadata(property.properties, enable_namespacing, parameter_name)
            )
        return parameters

    def get_payload_parameters(
        self, operation: "RestApiOperation", use_parameters_from_metadata: bool, enable_namespacing: bool
    ):
        """Get the payload parameters for the operation."""
        if use_parameters_from_metadata:
            if operation.request_body is None:
                raise Exception(
                    f"Payload parameters cannot be retrieved from the `{operation.Id}` "
                    f"operation payload metadata because it is missing."
                )
            if operation.request_body.media_type == RestApiOperation.MEDIA_TYPE_TEXT_PLAIN:
                return [self.create_payload_artificial_parameter(operation)]

            return self._get_parameters_from_payload_metadata(operation.request_body.properties, enable_namespacing)

        return [
            self.create_payload_artificial_parameter(operation),
            self.create_content_type_artificial_parameter(operation),
        ]

    def get_default_response(
        self, responses: dict[str, RestApiOperationExpectedResponse], preferred_responses: list[str]
    ) -> RestApiOperationExpectedResponse | None:
        """Get the default response for the operation.

        If no appropriate response is found, returns None.
        """
        for code in preferred_responses:
            if code in responses:
                return responses[code]
        return None

    def get_default_return_parameter(self, preferred_responses: list[str] | None = None) -> KernelParameterMetadata:
        """Get the default return parameter for the operation."""
        if preferred_responses is None:
            preferred_responses = self._preferred_responses

        rest_operation_response = self.get_default_response(self.responses, preferred_responses)

        if rest_operation_response:
            return KernelParameterMetadata(
                name="return",
                description=rest_operation_response.description,
                type_=rest_operation_response.schema.get("type") if rest_operation_response.schema else None,
                schema_data=rest_operation_response.schema,
            )

        return None
