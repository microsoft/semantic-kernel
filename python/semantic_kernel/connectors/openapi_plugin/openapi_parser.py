# Copyright (c) Microsoft. All rights reserved.

import logging
from collections import OrderedDict
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlparse

from prance import ResolvingParser

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_expected_response import (
    RestApiOperationExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter import RestApiOperationParameter
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter_location import (
    RestApiOperationParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_payload import RestApiOperationPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_payload_property import (
    RestApiOperationPayloadProperty,
)
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
        OpenAIFunctionExecutionParameters,
    )
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenApiParser:
    """NOTE: SK Python only supports the OpenAPI Spec >=3.0.

    Import an OpenAPI file.

    Args:
        openapi_file: The path to the OpenAPI file which can be local or a URL.

    Returns:
        The parsed OpenAPI file


    :param openapi_file: The path to the OpenAPI file which can be local or a URL.
    :return: The parsed OpenAPI file
    """

    PAYLOAD_PROPERTIES_HIERARCHY_MAX_DEPTH: int = 10
    SUPPORTED_MEDIA_TYPES: Final[list[str]] = ["application/json", "text/plain"]

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
            default_value = property_schema.get("default", None)

            property = RestApiOperationPayloadProperty(
                name=property_name,
                type=property_schema.get("type", None),
                is_required=property_name in required_properties,
                properties=self._get_payload_properties(operation_id, property_schema, required_properties, level + 1),
                description=property_schema.get("description", None),
                schema=property_schema,
                default_value=default_value,
            )

            result.append(property)

        return result

    def _create_rest_api_operation_payload(
        self, operation_id: str, request_body: dict[str, Any]
    ) -> RestApiOperationPayload:
        if request_body is None or request_body.get("content") is None:
            return None
        media_type = next((mt for mt in OpenApiParser.SUPPORTED_MEDIA_TYPES if mt in request_body.get("content")), None)
        if media_type is None:
            raise Exception(f"Neither of the media types of {operation_id} is supported.")
        media_type_metadata = request_body.get("content")[media_type]
        payload_properties = self._get_payload_properties(
            operation_id, media_type_metadata["schema"], media_type_metadata["schema"].get("required", set())
        )
        return RestApiOperationPayload(
            media_type,
            payload_properties,
            request_body.get("description"),
            schema=media_type_metadata.get("schema", None),
        )

    def _create_response(
        self, responses: dict[str, Any]
    ) -> Generator[tuple[str, RestApiOperationExpectedResponse], None, None]:
        for response_key, response_value in responses.items():
            media_type = next(
                (mt for mt in OpenApiParser.SUPPORTED_MEDIA_TYPES if mt in response_value.get("content", {})), None
            )
            if media_type is not None:
                matching_schema = response_value["content"][media_type].get("schema", {})
                description = response_value.get("description") or matching_schema.get("description", "")
                yield (
                    response_key,
                    RestApiOperationExpectedResponse(
                        description=description,
                        media_type=media_type,
                        schema=matching_schema if matching_schema else None,
                    ),
                )

    def create_rest_api_operations(
        self,
        parsed_document: Any,
        execution_settings: "OpenAIFunctionExecutionParameters | OpenAPIFunctionExecutionParameters | None" = None,
    ) -> dict[str, RestApiOperation]:
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
                responses = dict(self._create_response(details.get("responses", {})))

                rest_api_operation = RestApiOperation(
                    id=operationId,
                    method=request_method,
                    server_url=urlparse(base_url),
                    path=path,
                    params=parsed_params,
                    request_body=request_body,
                    summary=summary,
                    description=description,
                    responses=OrderedDict(responses),
                )

                request_objects[operationId] = rest_api_operation
        return request_objects
