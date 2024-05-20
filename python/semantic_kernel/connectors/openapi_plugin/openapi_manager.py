# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import json
import logging
import re
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Tuple
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import httpx
from openapi_core import Spec
from prance import ResolvingParser

from semantic_kernel.connectors.ai.open_ai.const import USER_AGENT
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException, PluginInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata

if TYPE_CHECKING:
    from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
        OpenAIFunctionExecutionParameters,
    )
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

logger: logging.Logger = logging.getLogger(__name__)


class RestApiOperationParameterStyle(Enum):
    SIMPLE = "simple"


class RestApiOperationPayloadProperty:
    def __init__(
        self,
        name: str,
        type: str,
        properties: RestApiOperationPayloadProperty,
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | None = None,
    ):
        self.name = name
        self.type = type
        self.properties = properties
        self.description = description
        self.is_required = is_required
        self.default_value = default_value
        self.schema = schema


class RestApiOperationPayload:
    def __init__(
        self,
        media_type: str,
        properties: list[RestApiOperationPayloadProperty],
        description: str | None = None,
        schema: str | None = None,
    ):
        self.media_type = media_type
        self.properties = properties
        self.description = description
        self.schema = schema


class RestApiOperation:
    MEDIA_TYPE_TEXT_PLAIN = "text/plain"
    PAYLOAD_ARGUMENT_NAME = "payload"
    CONTENT_TYPE_ARGUMENT_NAME = "content-type"
    INVALID_SYMBOLS_REGEX = re.compile(r"[^0-9A-Za-z_]+")

    def __init__(
        self,
        id: str,
        method: str,
        server_url: str,
        path: str,
        summary: str | None = None,
        description: str | None = None,
        params: list[RestApiOperationParameter] | None = None,
        request_body: RestApiOperationPayload | None = None,
    ):
        self.id = id
        self.method = method.upper()
        self.server_url = server_url
        self.path = path
        self.summary = summary
        self.description = description
        self.parameters = params
        self.request_body = request_body

    def url_join(self, base_url: str, path: str):
        """Join a base URL and a path, correcting for any missing slashes."""
        parsed_base = urlparse(base_url)
        if not parsed_base.path.endswith("/"):
            base_path = parsed_base.path + "/"
        else:
            base_path = parsed_base.path
        full_path = urljoin(base_path, path.lstrip("/"))
        return urlunparse(parsed_base._replace(path=full_path))

    def build_headers(self, arguments: Dict[str, Any]) -> Dict[str, str]:
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
        server_url = self.get_server_url(server_url_override, api_host_url)
        path = self.build_path(self.path, arguments)
        return urljoin(server_url.geturl(), path.lstrip("/"))

    def get_server_url(self, server_url_override=None, api_host_url=None):
        if server_url_override is not None and server_url_override.geturl() != b"":
            server_url_string = server_url_override.geturl()
        else:
            server_url_string = (
                self.server_url.geturl()
                if self.server_url
                else api_host_url.geturl() if api_host_url else self._raise_invalid_operation_exception()
            )

        # make sure the base URL ends with a trailing slash
        if not server_url_string.endswith("/"):
            server_url_string += "/"

        return urlparse(server_url_string)

    def build_path(self, path_template: str, arguments: Dict[str, Any]) -> str:
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

    def build_query_string(self, arguments: Dict[str, Any]) -> str:
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
        return RestApiOperation.INVALID_SYMBOLS_REGEX.sub("_", parameter_name)

    def get_parameters(
        self,
        operation: RestApiOperation,
        add_payload_params_from_metadata: bool = True,
        enable_payload_spacing: bool = False,
    ) -> list[RestApiOperationParameter]:
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

    def create_payload_artificial_parameter(self, operation: RestApiOperation) -> RestApiOperationParameter:
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

    def create_content_type_artificial_parameter(self) -> RestApiOperationParameter:
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
        properties: list[RestApiOperationPayloadProperty],
        enable_namespacing: bool = False,
        root_property_name: bool = None,
    ) -> list[RestApiOperationParameter]:
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
        self, operation: RestApiOperation, use_parameters_from_metadata: bool, enable_namespacing: bool
    ):
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


class RestApiOperationParameterLocation(Enum):
    """The location of the REST API operation parameter."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


class RestApiOperationParameter:
    def __init__(
        self,
        name: str,
        type: str,
        location: RestApiOperationParameterLocation,
        style: RestApiOperationParameterStyle | None = None,
        alternative_name: str | None = None,
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | None = None,
    ):

        self.name = name
        self.type = type
        self.location = location
        self.style = style
        self.alternative_name = alternative_name
        self.description = description
        self.is_required = is_required
        self.default_value = default_value
        self.schema = schema


class OpenApiParser:
    """
    NOTE: SK Python only supports the OpenAPI Spec >=3.0

    Import an OpenAPI file.

    Args:
        openapi_file: The path to the OpenAPI file which can be local or a URL.

    Returns:
        The parsed OpenAPI file


    :param openapi_file: The path to the OpenAPI file which can be local or a URL.
    :return: The parsed OpenAPI file
    """

    PAYLOAD_PROPERTIES_HIERARCHY_MAX_DEPTH = 10
    supported_media_types = ["application/json", "text/plain"]

    def parse(self, openapi_document: str) -> Any | dict[str, Any] | None:
        """Parse the OpenAPI document."""
        parser = ResolvingParser(openapi_document)
        return parser.specification

    def _parse_parameters(self, parameters: list[dict[str, Any]]):
        """Parse the parameters from the OpenAPI document."""
        result: list[RestApiOperationParameter] = []
        for param in parameters:
            name = param["name"]
            type = param["schema"]["type"]
            if not param.get("in"):
                raise PluginInitializationError(f"Parameter {name} is missing 'in' field")
            location = RestApiOperationParameterLocation(param["in"])
            description = param.get("description", None)
            is_required = param.get("required", False)
            default_value = param.get("default", None)
            schema = param.get("schema", None)
            schema_type = schema.get("type", None) if schema else "string"

            result.append(
                RestApiOperationParameter(
                    name=name,
                    type=type,
                    location=location,
                    description=description,
                    is_required=is_required,
                    default_value=default_value,
                    schema=schema_type,
                )
            )
        return result

    def _get_payload_properties(self, operation_id, schema, required_properties, level=0):
        if schema is None:
            return []

        if level > OpenApiParser.PAYLOAD_PROPERTIES_HIERARCHY_MAX_DEPTH:
            raise Exception(
                f"Max level {OpenApiParser.PAYLOAD_PROPERTIES_HIERARCHY_MAX_DEPTH} of "
                f"traversing payload properties of `{operation_id}` operation is exceeded."
            )

        result = []

        for property_name, property_schema in schema.get("properties", {}).items():
            property = RestApiOperationPayloadProperty(
                name=property_name,
                type=property_schema.get("type", None),
                is_required=property_name in required_properties,
                properties=self._get_payload_properties(operation_id, property_schema, required_properties, level + 1),
                description=property_schema.get("description", None),
                schema="str",  # TODO - add support for JSON schema?
                default_value="str",  # TODO - add support for default values?
            )

            result.append(property)

        return result

    def _create_rest_api_operation_payload(
        self, operation_id: str, request_body: dict[str, Any]
    ) -> RestApiOperationPayload:
        if request_body is None or request_body.get("content") is None:
            return None
        media_type = next((mt for mt in OpenApiParser.supported_media_types if mt in request_body.get("content")), None)
        if media_type is None:
            raise Exception(f"Neither of the media types of {operation_id} is supported.")
        media_type_metadata = request_body.get("content")[media_type]
        payload_properties = self._get_payload_properties(
            operation_id, media_type_metadata["schema"], media_type_metadata["schema"].get("required", set())
        )
        return RestApiOperationPayload(
            media_type,
            payload_properties,
            request_body.get("description", None),
            schema="str",  # TODO - add support for JSON schema?
        )

    def create_rest_api_operations(
        self,
        parsed_document: Any,
        execution_settings: "OpenAIFunctionExecutionParameters | OpenAPIFunctionExecutionParameters | None" = None,
    ) -> Dict[str, RestApiOperation]:
        """Create the REST API Operations from the parsed OpenAPI document.

        Args:
            parsed_document: The parsed OpenAPI document
            execution_settings: The execution settings

        Returns:
            A dictionary of RestApiOperation objects keyed by operationId
        """
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

                parsed_params = self._parse_parameters(parameters)
                request_body = self._create_rest_api_operation_payload(operationId, details.get("requestBody", None))

                rest_api_operation = RestApiOperation(
                    id=operationId,
                    method=request_method,
                    server_url=urlparse(base_url),
                    path=path,
                    params=parsed_params,
                    request_body=request_body,
                    summary=summary,
                    description=description,
                )

                request_objects[operationId] = rest_api_operation
        return request_objects


class Uri:
    """The Uri class that represents the URI."""

    def __init__(self, uri):
        self.uri = uri

    def get_left_part(self):
        parsed_uri = urlparse(self.uri)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"


class RestApiOperationRunOptions:
    """The options for running the REST API operation."""

    def __init__(self, server_url_override=None, api_host_url=None):
        self.server_url_override: str = server_url_override
        self.api_host_url: str = api_host_url


class OpenApiRunner:
    """The OpenApiRunner that runs the operations defined in the OpenAPI manifest"""

    payload_argument_name = "payload"
    media_type_application_json = "application/json"

    def __init__(
        self,
        parsed_openapi_document: Mapping[str, str],
        auth_callback: Callable[[Dict[str, str]], Dict[str, str]] | None = None,
        http_client: httpx.AsyncClient | None = None,
        enable_dynamic_payload: bool = True,
        enable_payload_namespacing: bool = False,
    ):
        self.spec = Spec.from_dict(parsed_openapi_document)
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

    def build_json_payload(
        self, payload_metadata: RestApiOperationPayload, arguments: Dict[str, Any]
    ) -> Tuple[str, str]:
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

    def build_operation_payload(self, operation: RestApiOperation, arguments: KernelArguments) -> Tuple[str, str]:
        if operation.request_body is None and self.payload_argument_name not in arguments:
            return None, None
        return self.build_json_payload(operation.request_body, arguments)

    def get_argument_name_for_payload(self, property_name, property_namespace=None):
        if not self.enable_payload_namespacing:
            return property_name
        return f"{property_namespace}.{property_name}" if property_namespace else property_name

    async def run_operation(
        self,
        operation: RestApiOperation,
        arguments: KernelArguments | None = None,
        options: RestApiOperationRunOptions | None = None,
    ) -> str:
        from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT

        url = self.build_operation_url(
            operation=operation,
            arguments=arguments,
            server_url_override=options.server_url_override,
            api_host_url=options.api_host_url,
        )
        headers = operation.build_headers(arguments=arguments)
        payload, _ = self.build_operation_payload(operation=operation, arguments=arguments)

        """Runs the operation defined in the OpenAPI manifest"""
        if headers is None:
            headers = {}

        if self.auth_callback:
            headers_update = await self.auth_callback(headers=headers)
            headers.update(headers_update)

        headers[USER_AGENT] = " ".join((HTTP_USER_AGENT, headers.get(USER_AGENT, ""))).rstrip()

        if "Content-Type" not in headers:
            headers["Content-Type"] = self.media_type_application_json

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
            else:
                async with httpx.AsyncClient() as client:
                    return await make_request(client)

        return await fetch()


def create_functions_from_openapi(
    plugin_name: str,
    openapi_document_path: str,
    execution_settings: "OpenAIFunctionExecutionParameters | OpenAPIFunctionExecutionParameters | None" = None,
) -> list[KernelFunctionFromMethod]:
    """Creates the functions from OpenAPI document.

    Args:
        plugin_name: The name of the plugin
        openapi_document_path: The OpenAPI document path, it must be a file path to the spec.
        execution_settings: The execution settings

    Returns:
        list[KernelFunctionFromMethod]: the operations as functions
    """
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document_path)
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=execution_settings)

    auth_callback = None
    if execution_settings and execution_settings.auth_callback:
        auth_callback = execution_settings.auth_callback
    openapi_runner = OpenApiRunner(
        parsed_openapi_document=parsed_doc,
        auth_callback=auth_callback,
        http_client=execution_settings.http_client if execution_settings else None,
        enable_dynamic_payload=execution_settings.enable_dynamic_payload if execution_settings else True,
        enable_payload_namespacing=execution_settings.enable_payload_namespacing if execution_settings else False,
    )

    return [
        _create_function_from_operation(openapi_runner, operation, plugin_name, execution_parameters=execution_settings)
        for operation in operations.values()
    ]


def _create_function_from_operation(
    runner: OpenApiRunner,
    operation: RestApiOperation,
    plugin_name: str | None = None,
    execution_parameters: "OpenAIFunctionExecutionParameters | OpenAPIFunctionExecutionParameters | None" = None,
    document_uri: str | None = None,
) -> KernelFunctionFromMethod:
    logger.info(f"Registering OpenAPI operation: {plugin_name}.{operation.id}")

    rest_operation_params: list[RestApiOperationParameter] = operation.get_parameters(
        operation=operation,
        add_payload_params_from_metadata=getattr(execution_parameters, "enable_dynamic_payload", True),
        enable_payload_spacing=getattr(execution_parameters, "enable_payload_namespacing", False),
    )

    @kernel_function(
        description=operation.summary if operation.summary else operation.description,
        name=operation.id,
    )
    async def run_openapi_operation(
        **kwargs: dict[str, Any],
    ) -> str:
        try:
            kernel_arguments = KernelArguments()

            for parameter in rest_operation_params:
                if parameter.alternative_name and parameter.alternative_name in kwargs:
                    value = kwargs[parameter.alternative_name]
                    if value is not None:
                        kernel_arguments[parameter.name] = value
                        continue

                if parameter.name in kwargs:
                    value = kwargs[parameter.name]
                    if value is not None:
                        kernel_arguments[parameter.name] = value
                        continue

                if parameter.is_required:
                    raise FunctionExecutionException(
                        f"No variable found in context to use as an argument for the "
                        f"`{parameter.name}` parameter of the `{plugin_name}.{operation.id}` REST function."
                    )

            options = RestApiOperationRunOptions(
                server_url_override=(
                    urlparse(execution_parameters.server_url_override) if execution_parameters else None
                ),
                api_host_url=Uri(document_uri).get_left_part() if document_uri is not None else None,
            )

            response = await runner.run_operation(operation, kernel_arguments, options)
            return response
        except Exception as e:
            logger.error(f"Error running OpenAPI operation: {operation.id}", exc_info=True)
            raise FunctionExecutionException(f"Error running OpenAPI operation: {operation.id}") from e

    parameters: list[KernelParameterMetadata] = [
        KernelParameterMetadata(
            name=p.alternative_name or p.name,
            description=f"{p.description or p.name}",
            default_value=p.default_value or "",
            is_required=p.is_required,
            type="str" if p.type == "string" else "bool" if p.type == "boolean" else "object",
        )
        for p in rest_operation_params
    ]

    additional_metadata = {"method": operation.method.upper()}

    return KernelFunctionFromMethod(
        method=run_openapi_operation,
        plugin_name=plugin_name,
        parameters=parameters,
        additional_metadata=additional_metadata,
    )
