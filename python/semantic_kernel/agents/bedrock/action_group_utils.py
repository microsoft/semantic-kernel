# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def kernel_function_to_bedrock_function_schema(
    function_choice_configuration: FunctionCallChoiceConfiguration,
) -> dict[str, Any]:
    """Convert the kernel function to bedrock function schema."""
    return {
        "functions": [
            kernel_function_metadata_to_bedrock_function_schema(function_metadata)
            for function_metadata in function_choice_configuration.available_functions or []
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
        # This field controls whether user confirmation is required to invoke the function.
        # If this is set to "ENABLED", the user will be prompted to confirm the function invocation.
        # Only after the user confirms, the function call request will be issued by the agent.
        # If the user denies the confirmation, the agent will act as if the function does not exist.
        # Currently, we do not support this feature, so we set it to "DISABLED".
        "requireConfirmation": "DISABLED",
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


# These are the allowed parameter types in bedrock function.
# https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_ParameterDetail.html
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


def parse_return_control_payload(return_control_payload: dict[str, Any]) -> list[FunctionCallContent]:
    """Parse the return control payload to a list of function call contents for the kernel."""
    return [
        FunctionCallContent(
            id=return_control_payload["invocationId"],
            name=invocation_input["functionInvocationInput"]["function"],
            arguments={
                parameter["name"]: parameter["value"]
                for parameter in invocation_input["functionInvocationInput"]["parameters"]
            },
            metadata=invocation_input,
        )
        for invocation_input in return_control_payload.get("invocationInputs", [])
    ]


def parse_function_result_contents(function_result_contents: list[FunctionResultContent]) -> list[dict[str, Any]]:
    """Parse the function result contents to be returned to the agent in the session state."""
    return [
        {
            "functionResult": {
                "actionGroup": function_result_content.metadata["functionInvocationInput"]["actionGroup"],
                "function": function_result_content.name,
                "responseBody": {"TEXT": {"body": str(function_result_content.result)}},
            }
        }
        for function_result_content in function_result_contents
    ]
