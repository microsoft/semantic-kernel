# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def kernel_function_to_bedrock_function_schema(
    function_choice_configuration: FunctionCallChoiceConfiguration,
) -> dict[str, Any]:
    """Convert the kernel function to bedrock function schema."""
    return {
        "functions": [
            kernel_function_metadata_to_bedrock_function_schema(function_metadata)
            for function_metadata in function_choice_configuration.available_functions
        ]
    }


def kernel_function_metadata_to_bedrock_function_schema(function_metadata: KernelFunctionMetadata) -> dict[str, Any]:
    """Convert the kernel function metadata to bedrock function schema."""
    schema = {
        "description": function_metadata.description,
        "name": function_metadata.fully_qualified_name,
        "parameters": {
            parameter.name: kernel_function_parameter_to_bedrock_function_parameter(parameter)
            for parameter in function_metadata.parameters
        },
    }

    # Remove None values from the schema
    return {key: value for key, value in schema.items() if value is not None}


def kernel_function_parameter_to_bedrock_function_parameter(parameter: KernelParameterMetadata):
    """Convert the kernel function parameters to bedrock function parameters."""
    schema = {
        "description": parameter.description,
        "type": kernel_function_parameter_type_to_bedrock_function_parameter_type(parameter.schema_data),
        "required": parameter.is_required,
    }

    # Remove None values from the schema
    return {key: value for key, value in schema.items() if value is not None}


BEDROCK_FUNCTION_ALLOWED_PARAMETER_TYPES = {
    "string",
    "number",
    "integer",
    "boolean",
    "array",
}


def kernel_function_parameter_type_to_bedrock_function_parameter_type(schema_data: dict[str, Any] | None) -> str:
    """Convert the kernel function parameter type to bedrock function parameter type."""
    if schema_data is None:
        raise ValueError(
            "Schema data is required to convert the kernel function parameter type to bedrock function parameter type."
        )

    type_ = schema_data.get("type")
    if type_ is None:
        raise ValueError(
            "Type is required to convert the kernel function parameter type to bedrock function parameter type."
        )

    if type_ not in BEDROCK_FUNCTION_ALLOWED_PARAMETER_TYPES:
        raise ValueError(
            f"Type {type_} is not allowed in bedrock function parameter type. "
            f"Allowed types are {BEDROCK_FUNCTION_ALLOWED_PARAMETER_TYPES}."
        )

    return type_
