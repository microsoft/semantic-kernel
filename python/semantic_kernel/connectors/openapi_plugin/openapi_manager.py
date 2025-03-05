# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from semantic_kernel.connectors.openapi_plugin.const import OperationExtensions
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter import RestApiParameter
from semantic_kernel.connectors.openapi_plugin.models.rest_api_run_options import RestApiRunOptions
from semantic_kernel.connectors.openapi_plugin.models.rest_api_security_requirement import RestApiSecurityRequirement
from semantic_kernel.connectors.openapi_plugin.models.rest_api_uri import Uri
from semantic_kernel.connectors.openapi_plugin.openapi_parser import OpenApiParser
from semantic_kernel.connectors.openapi_plugin.openapi_runner import OpenApiRunner
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.schema.kernel_json_schema_builder import TYPE_MAPPING
from semantic_kernel.utils.experimental_decorator import experimental_function

if TYPE_CHECKING:
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

logger: logging.Logger = logging.getLogger(__name__)


@experimental_function
def create_functions_from_openapi(
    plugin_name: str,
    openapi_document_path: str | None = None,
    openapi_parsed_spec: dict[str, Any] | None = None,
    execution_settings: "OpenAPIFunctionExecutionParameters | None" = None,
) -> list[KernelFunctionFromMethod]:
    """Creates the functions from OpenAPI document.

    Args:
        plugin_name: The name of the plugin
        openapi_document_path: The OpenAPI document path, it must be a file path to the spec (optional)
        openapi_parsed_spec: The parsed OpenAPI spec (optional)
        execution_settings: The execution settings

    Returns:
        list[KernelFunctionFromMethod]: the operations as functions
    """
    parsed_doc: dict[str, Any] | Any = None
    if openapi_parsed_spec is not None:
        parsed_doc = openapi_parsed_spec
    else:
        if openapi_document_path is None:
            raise FunctionExecutionException(
                "Either `openapi_document_path` or `openapi_parsed_spec` must be provided."
            )

        # Parse the document from the given path
        parser = OpenApiParser()
        parsed_doc = parser.parse(openapi_document_path)
        if parsed_doc is None:
            raise FunctionExecutionException(f"Error parsing OpenAPI document: {openapi_document_path}")

    parser = OpenApiParser()
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=execution_settings)

    global_security_requirements = parsed_doc.get("security", [])

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

    functions = []
    for operation in operations.values():
        try:
            kernel_function = _create_function_from_operation(
                openapi_runner,
                operation,
                plugin_name,
                execution_parameters=execution_settings,
                security=global_security_requirements,
            )
            functions.append(kernel_function)
            operation.freeze()
        except Exception as ex:
            error_msg = f"Error while registering Rest function {plugin_name}.{operation.id}: {ex}"
            logger.error(error_msg)
            raise FunctionExecutionException(error_msg) from ex

    return functions


@experimental_function
def _create_function_from_operation(
    runner: OpenApiRunner,
    operation: RestApiOperation,
    plugin_name: str | None = None,
    execution_parameters: "OpenAPIFunctionExecutionParameters | None" = None,
    document_uri: str | None = None,
    security: list[RestApiSecurityRequirement] | None = None,
) -> KernelFunctionFromMethod:
    logger.info(f"Registering OpenAPI operation: {plugin_name}.{operation.id}")

    rest_operation_params: list[RestApiParameter] = operation.get_parameters(
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

            options = RestApiRunOptions(
                server_url_override=(
                    urlparse(execution_parameters.server_url_override) if execution_parameters else None
                ),
                api_host_url=Uri(document_uri).get_left_part() if document_uri is not None else None,
            )

            return await runner.run_operation(operation, kernel_arguments, options)
        except Exception as e:
            logger.error(f"Error running OpenAPI operation: {operation.id}", exc_info=True)
            raise FunctionExecutionException(f"Error running OpenAPI operation: {operation.id}") from e

    parameters: list[KernelParameterMetadata] = [
        KernelParameterMetadata(
            name=p.alternative_name or p.name,
            description=f"{p.description or p.name}",
            default_value=p.default_value or "",
            is_required=p.is_required,
            type_=p.type if p.type is not None else TYPE_MAPPING.get(p.type, "object"),
            schema_data=(
                p.schema
                if p.schema is not None and isinstance(p.schema, dict)
                else {"type": f"{p.type}"}
                if p.type
                else None
            ),
        )
        for p in rest_operation_params
    ]

    return_parameter = operation.get_default_return_parameter()

    additional_metadata = {
        OperationExtensions.METHOD_KEY.value: operation.method.upper(),
        OperationExtensions.OPERATION_KEY.value: operation,
        OperationExtensions.SERVER_URLS_KEY.value: (
            [operation.servers[0]["url"]]
            if operation.servers and len(operation.servers) > 0 and operation.servers[0]["url"]
            else []
        ),
    }

    if security is not None:
        additional_metadata[OperationExtensions.SECURITY_KEY.value] = security

    return KernelFunctionFromMethod(
        method=run_openapi_operation,
        plugin_name=plugin_name,
        parameters=parameters,
        return_parameter=return_parameter,
        additional_metadata=additional_metadata,
    )
