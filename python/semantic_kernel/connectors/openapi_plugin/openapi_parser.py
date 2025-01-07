# Copyright (c) Microsoft. All rights reserved.

import logging
from collections import OrderedDict
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Final

from prance import ResolvingParser

from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter import RestApiParameter
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_location import (
    RestApiParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload_property import (
    RestApiPayloadProperty,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_security_requirement import RestApiSecurityRequirement
from semantic_kernel.connectors.openapi_plugin.models.rest_api_security_scheme import RestApiSecurityScheme
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError

if TYPE_CHECKING:
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

logger: logging.Logger = logging.getLogger(__name__)


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
        result: list[RestApiParameter] = []
        for param in parameters:
            name: str = param["name"]
            if not param.get("in"):
                raise PluginInitializationError(f"Parameter {name} is missing 'in' field")
            if param.get("content", None) is not None:
                # The schema and content fields are mutually exclusive.
                raise PluginInitializationError(f"Parameter {name} cannot have a 'content' field. Expected: schema.")
            location = RestApiParameterLocation(param["in"])
            description: str = param.get("description", None)
            is_required: bool = param.get("required", False)
            default_value = param.get("default", None)
            schema: dict[str, Any] | None = param.get("schema", None)

            result.append(
                RestApiParameter(
                    name=name,
                    type=schema.get("type", "string") if schema else "string",
                    location=location,
                    description=description,
                    is_required=is_required,
                    default_value=default_value,
                    schema=schema if schema else {"type": "string"},
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

            property = RestApiPayloadProperty(
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
    ) -> RestApiPayload | None:
        if request_body is None or request_body.get("content") is None:
            return None

        content = request_body.get("content")
        if content is None:
            return None

        media_type = next((mt for mt in OpenApiParser.SUPPORTED_MEDIA_TYPES if mt in content), None)
        if media_type is None:
            raise Exception(f"Neither of the media types of {operation_id} is supported.")

        media_type_metadata = content[media_type]
        payload_properties = self._get_payload_properties(
            operation_id, media_type_metadata["schema"], media_type_metadata["schema"].get("required", set())
        )
        return RestApiPayload(
            media_type,
            payload_properties,
            request_body.get("description"),
            schema=media_type_metadata.get("schema", None),
        )

    def _create_response(self, responses: dict[str, Any]) -> Generator[tuple[str, RestApiExpectedResponse], None, None]:
        for response_key, response_value in responses.items():
            media_type = next(
                (mt for mt in OpenApiParser.SUPPORTED_MEDIA_TYPES if mt in response_value.get("content", {})), None
            )
            if media_type is not None:
                matching_schema = response_value["content"][media_type].get("schema", {})
                description = response_value.get("description") or matching_schema.get("description", "")
                yield (
                    response_key,
                    RestApiExpectedResponse(
                        description=description,
                        media_type=media_type,
                        schema=matching_schema if matching_schema else None,
                    ),
                )

    def _parse_security_schemes(self, components: dict) -> dict[str, dict]:
        security_schemes = {}
        schemes = components.get("securitySchemes", {})
        for scheme_name, scheme_data in schemes.items():
            security_schemes[scheme_name] = scheme_data
        return security_schemes

    def _create_rest_api_security_scheme(self, security_scheme_data: dict) -> RestApiSecurityScheme:
        return RestApiSecurityScheme(
            security_scheme_type=security_scheme_data.get("type", ""),
            description=security_scheme_data.get("description"),
            name=security_scheme_data.get("name", ""),
            in_=security_scheme_data.get("in", ""),
            scheme=security_scheme_data.get("scheme", ""),
            bearer_format=security_scheme_data.get("bearerFormat"),
            flows=security_scheme_data.get("flows"),
            open_id_connect_url=security_scheme_data.get("openIdConnectUrl", ""),
        )

    def _create_security_requirements(
        self,
        security: list[dict[str, list[str]]],
        security_schemes: dict[str, dict],
    ) -> list[RestApiSecurityRequirement]:
        security_requirements: list[RestApiSecurityRequirement] = []

        for requirement in security:
            for scheme_name, scopes in requirement.items():
                scheme_data = security_schemes.get(scheme_name)
                if not scheme_data:
                    raise PluginInitializationError(f"Security scheme '{scheme_name}' is not defined in components.")
                scheme = self._create_rest_api_security_scheme(scheme_data)
                security_requirements.append(RestApiSecurityRequirement({scheme: scopes}))

        return security_requirements

    def create_rest_api_operations(
        self,
        parsed_document: Any,
        execution_settings: "OpenAPIFunctionExecutionParameters | None" = None,
    ) -> dict[str, RestApiOperation]:
        """Create REST API operations from the parsed OpenAPI document.

        Args:
            parsed_document: The parsed OpenAPI document.
            execution_settings: The execution settings.

        Returns:
            A dictionary of RestApiOperation instances.
        """
        from semantic_kernel.connectors.openapi_plugin import OperationSelectionPredicateContext

        components = parsed_document.get("components", {})
        security_schemes = self._parse_security_schemes(components)

        paths = parsed_document.get("paths", {})
        request_objects = {}

        servers = parsed_document.get("servers", [])

        server_urls: list[dict[str, Any]] = []

        if execution_settings and execution_settings.server_url_override:
            # Override the servers with the provided URL
            server_urls = [{"url": execution_settings.server_url_override, "variables": {}}]
        elif servers:
            # Process servers, ensuring we capture their variables
            for server in servers:
                server_entry = {
                    "url": server.get("url", "/"),
                    "variables": server.get("variables", {}),
                    "description": server.get("description", ""),
                }
                server_urls.append(server_entry)
        else:
            # Default server if none specified
            server_urls = [{"url": "/", "variables": {}, "description": ""}]

        for path, methods in paths.items():
            for method, details in methods.items():
                request_method = method.lower()
                operationId = details.get("operationId", path + "_" + request_method)

                summary = details.get("summary", None)
                description = details.get("description", None)

                context = OperationSelectionPredicateContext(operationId, path, method, description)
                if (
                    execution_settings
                    and execution_settings.operation_selection_predicate
                    and not execution_settings.operation_selection_predicate(context)
                ):
                    logger.info(f"Skipping operation {operationId} based on custom predicate.")
                    continue

                if execution_settings and operationId in execution_settings.operations_to_exclude:
                    logger.info(f"Skipping operation {operationId} as it is excluded.")
                    continue

                parameters = details.get("parameters", [])
                parsed_params = self._parse_parameters(parameters)
                request_body = self._create_rest_api_operation_payload(operationId, details.get("requestBody", None))
                responses = dict(self._create_response(details.get("responses", {})))

                operation_security = details.get("security", [])
                security_requirements = self._create_security_requirements(operation_security, security_schemes)

                rest_api_operation = RestApiOperation(
                    id=operationId,
                    method=request_method,
                    servers=server_urls,
                    path=path,
                    params=parsed_params,
                    request_body=request_body,
                    summary=summary,
                    description=description,
                    responses=OrderedDict(responses),
                    security_requirements=security_requirements,
                )

                request_objects[operationId] = rest_api_operation
        return request_objects
