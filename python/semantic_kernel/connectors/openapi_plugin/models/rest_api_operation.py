# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Any, Final
from urllib.parse import ParseResult, ParseResultBytes, urlencode, urljoin, urlparse, urlunparse

from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter import RestApiParameter
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_location import (
    RestApiParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_style import (
    RestApiParameterStyle,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload_property import (
    RestApiPayloadProperty,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_security_requirement import RestApiSecurityRequirement
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiOperation:
    """RestApiOperation."""

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
        servers: list[dict[str, Any]],
        path: str,
        summary: str | None = None,
        description: str | None = None,
        params: list["RestApiParameter"] | None = None,
        request_body: "RestApiPayload | None" = None,
        responses: dict[str, "RestApiExpectedResponse"] | None = None,
        security_requirements: list[RestApiSecurityRequirement] | None = None,
    ):
        """Initialize the RestApiOperation."""
        self._id = id
        self._method = method.upper()
        self._servers = servers
        self._path = path
        self._summary = summary
        self._description = description
        self._parameters = params if params else []
        self._request_body = request_body
        self._responses = responses
        self._security_requirements = security_requirements
        self._is_frozen = False

    def freeze(self):
        """Make the instance and its components immutable."""
        self._is_frozen = True

        if self.request_body:
            self.request_body.freeze()

        for param in self.parameters:
            param.freeze()

    def _throw_if_frozen(self):
        """Raise an exception if the object is frozen."""
        if self._is_frozen:
            raise FunctionExecutionException(
                f"The `RestApiOperation` instance with id {self.id} is frozen and cannot be modified."
            )

    @property
    def id(self):
        """Get the ID of the operation."""
        return self._id

    @id.setter
    def id(self, value: str):
        self._throw_if_frozen()
        self._id = value

    @property
    def method(self):
        """Get the method of the operation."""
        return self._method

    @method.setter
    def method(self, value: str):
        self._throw_if_frozen()
        self._method = value

    @property
    def servers(self):
        """Get the servers of the operation."""
        return self._servers

    @servers.setter
    def servers(self, value: list[dict[str, Any]]):
        self._throw_if_frozen()
        self._servers = value

    @property
    def path(self):
        """Get the path of the operation."""
        return self._path

    @path.setter
    def path(self, value: str):
        self._throw_if_frozen()
        self._path = value

    @property
    def summary(self):
        """Get the summary of the operation."""
        return self._summary

    @summary.setter
    def summary(self, value: str | None):
        self._throw_if_frozen()
        self._summary = value

    @property
    def description(self):
        """Get the description of the operation."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._throw_if_frozen()
        self._description = value

    @property
    def parameters(self):
        """Get the parameters of the operation."""
        return self._parameters

    @parameters.setter
    def parameters(self, value: list["RestApiParameter"]):
        self._throw_if_frozen()
        self._parameters = value

    @property
    def request_body(self):
        """Get the request body of the operation."""
        return self._request_body

    @request_body.setter
    def request_body(self, value: "RestApiPayload | None"):
        self._throw_if_frozen()
        self._request_body = value

    @property
    def responses(self):
        """Get the responses of the operation."""
        return self._responses

    @responses.setter
    def responses(self, value: dict[str, "RestApiExpectedResponse"] | None):
        self._throw_if_frozen()
        self._responses = value

    @property
    def security_requirements(self):
        """Get the security requirements of the operation."""
        return self._security_requirements

    @security_requirements.setter
    def security_requirements(self, value: list[RestApiSecurityRequirement] | None):
        self._throw_if_frozen()
        self._security_requirements = value

    def url_join(self, base_url: str, path: str):
        """Join a base URL and a path, correcting for any missing slashes."""
        parsed_base = urlparse(base_url)
        base_path = parsed_base.path + "/" if not parsed_base.path.endswith("/") else parsed_base.path
        full_path = urljoin(base_path, path.lstrip("/"))
        return urlunparse(parsed_base._replace(path=full_path))

    def build_headers(self, arguments: dict[str, Any]) -> dict[str, str]:
        """Build the headers for the operation."""
        headers = {}

        parameters = [p for p in self.parameters if p.location == RestApiParameterLocation.HEADER]

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
        try:
            return urljoin(server_url, path.lstrip("/"))
        except Exception as e:
            raise FunctionExecutionException(f"Error building the URL for the operation {self.id}: {e!s}") from e

    def get_server_url(self, server_url_override=None, api_host_url=None, arguments=None):
        """Get the server URL for the operation."""
        if arguments is None:
            arguments = {}

        # Prioritize server_url_override
        if (
            server_url_override is not None
            and isinstance(server_url_override, (ParseResult, ParseResultBytes))
            and server_url_override.geturl() != b""
        ):
            server_url_string = server_url_override.geturl()
        elif server_url_override is not None and isinstance(server_url_override, str) and server_url_override != "":
            server_url_string = server_url_override
        elif self.servers and len(self.servers) > 0:
            # Use the first server by default
            server = self.servers[0]
            server_url_string = server["url"] if isinstance(server, dict) else server
            server_variables = server.get("variables", {}) if isinstance(server, dict) else {}

            # Substitute server variables if available
            for variable_name, variable_def in server_variables.items():
                argument_name = variable_def.get("argument_name", variable_name)
                if argument_name in arguments:
                    value = arguments[argument_name]
                    server_url_string = server_url_string.replace(f"{{{variable_name}}}", value)
                elif "default" in variable_def and variable_def["default"] is not None:
                    # Use the default value if no argument is provided
                    value = variable_def["default"]
                    server_url_string = server_url_string.replace(f"{{{variable_name}}}", value)
                else:
                    # Raise an exception if no value is available
                    raise FunctionExecutionException(
                        f"No argument provided for the '{variable_name}' server variable of the operation '{self.id}'."
                    )
        elif self.server_url:
            server_url_string = self.server_url
        elif api_host_url is not None:
            server_url_string = api_host_url
        else:
            raise FunctionExecutionException(f"No valid server URL for operation {self.id}")

        # Ensure the base URL ends with a trailing slash
        if not server_url_string.endswith("/"):
            server_url_string += "/"

        return server_url_string  # Return the URL string directly

    def build_path(self, path_template: str, arguments: dict[str, Any]) -> str:
        """Build the path for the operation."""
        parameters = [p for p in self.parameters if p.location == RestApiParameterLocation.PATH]
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
        parameters = [p for p in self.parameters if p.location == RestApiParameterLocation.QUERY]
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
    ) -> list["RestApiParameter"]:
        """Get the parameters for the operation."""
        params = list(operation.parameters) if operation.parameters is not None else []
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

    def create_payload_artificial_parameter(self, operation: "RestApiOperation") -> "RestApiParameter":
        """Create an artificial parameter for the REST API request body."""
        return RestApiParameter(
            name=self.PAYLOAD_ARGUMENT_NAME,
            type=(
                "string"
                if operation.request_body
                and operation.request_body.media_type == RestApiOperation.MEDIA_TYPE_TEXT_PLAIN
                else "object"
            ),
            is_required=True,
            location=RestApiParameterLocation.BODY,
            style=RestApiParameterStyle.SIMPLE,
            description=operation.request_body.description if operation.request_body else "REST API request body.",
            schema=operation.request_body.schema if operation.request_body else None,
        )

    def create_content_type_artificial_parameter(self) -> "RestApiParameter":
        """Create an artificial parameter for the content type of the REST API request body."""
        return RestApiParameter(
            name=self.CONTENT_TYPE_ARGUMENT_NAME,
            type="string",
            is_required=False,
            location=RestApiParameterLocation.BODY,
            style=RestApiParameterStyle.SIMPLE,
            description="Content type of REST API request body.",
        )

    def _get_property_name(self, property: RestApiPayloadProperty, root_property_name: bool, enable_namespacing: bool):
        if enable_namespacing and root_property_name:
            return f"{root_property_name}.{property.name}"
        return property.name

    def _get_parameters_from_payload_metadata(
        self,
        properties: list["RestApiPayloadProperty"],
        enable_namespacing: bool = False,
        root_property_name: bool | None = None,
    ) -> list["RestApiParameter"]:
        parameters: list[RestApiParameter] = []
        for property in properties:
            parameter_name = self._get_property_name(property, root_property_name or False, enable_namespacing)
            if not hasattr(property, "properties") or not property.properties:
                parameters.append(
                    RestApiParameter(
                        name=parameter_name,
                        type=property.type,
                        is_required=property.is_required,
                        location=RestApiParameterLocation.BODY,
                        style=RestApiParameterStyle.SIMPLE,
                        description=property.description,
                        schema=property.schema,
                    )
                )
            else:
                # Handle property.properties as a single instance or a list
                if isinstance(property.properties, RestApiPayloadProperty):
                    nested_properties = [property.properties]
                else:
                    nested_properties = property.properties

                parameters.extend(
                    self._get_parameters_from_payload_metadata(nested_properties, enable_namespacing, parameter_name)
                )
        return parameters

    def get_payload_parameters(
        self, operation: "RestApiOperation", use_parameters_from_metadata: bool, enable_namespacing: bool
    ):
        """Get the payload parameters for the operation."""
        if use_parameters_from_metadata:
            if operation.request_body is None:
                raise Exception(
                    f"Payload parameters cannot be retrieved from the `{operation.id}` "
                    f"operation payload metadata because it is missing."
                )
            if operation.request_body.media_type == RestApiOperation.MEDIA_TYPE_TEXT_PLAIN:
                return [self.create_payload_artificial_parameter(operation)]

            return self._get_parameters_from_payload_metadata(operation.request_body.properties, enable_namespacing)

        return [
            self.create_payload_artificial_parameter(operation),
            self.create_content_type_artificial_parameter(),
        ]

    def get_default_response(
        self, responses: dict[str, RestApiExpectedResponse], preferred_responses: list[str]
    ) -> RestApiExpectedResponse | None:
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

        responses = self.responses if self.responses is not None else {}

        rest_operation_response = self.get_default_response(responses, preferred_responses)

        schema_type = None
        if rest_operation_response is not None and rest_operation_response.schema is not None:
            schema_type = rest_operation_response.schema.get("type")

        if rest_operation_response:
            return KernelParameterMetadata(
                name="return",
                description=rest_operation_response.description,
                type_=schema_type,
                schema_data=rest_operation_response.schema,
            )

        return KernelParameterMetadata(
            name="return",
            description="Default return parameter",
            type_="string",
            schema_data={"type": "string"},
        )
