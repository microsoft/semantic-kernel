# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.agents.bedrock.action_group_utils import (
    kernel_function_to_bedrock_function_schema,
    kernel_function_metadata_to_bedrock_function_schema,
    kernel_function_parameter_to_bedrock_function_parameter,
    kernel_function_parameter_type_to_bedrock_function_parameter_type,
    parse_return_control_payload,
    parse_function_result_contents,
)
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_kernel_function_to_bedrock_function_schema():
    # Test the conversion of kernel function to bedrock function schema
    function_metadata = KernelFunctionMetadata(
        description="Test function",
        fully_qualified_name="test_function",
        parameters=[
            KernelParameterMetadata(name="param1", description="Parameter 1", schema_data={"type": "string"}, is_required=True)
        ],
    )
    function_choice_configuration = FunctionCallChoiceConfiguration(available_functions=[function_metadata])
    result = kernel_function_to_bedrock_function_schema(function_choice_configuration)
    assert result == {
        "functions": [
            {
                "description": "Test function",
                "name": "test_function",
                "parameters": {
                    "param1": {
                        "description": "Parameter 1",
                        "type": "string",
                        "required": True,
                    }
                },
                "requireConfirmation": "DISABLED",
            }
        ]
    }


def test_kernel_function_metadata_to_bedrock_function_schema():
    # Test the conversion of kernel function metadata to bedrock function schema
    function_metadata = KernelFunctionMetadata(
        description="Test function",
        fully_qualified_name="test_function",
        parameters=[
            KernelParameterMetadata(name="param1", description="Parameter 1", schema_data={"type": "string"}, is_required=True)
        ],
    )
    result = kernel_function_metadata_to_bedrock_function_schema(function_metadata)
    assert result == {
        "description": "Test function",
        "name": "test_function",
        "parameters": {
            "param1": {
                "description": "Parameter 1",
                "type": "string",
                "required": True,
            }
        },
        "requireConfirmation": "DISABLED",
    }


def test_kernel_function_parameter_to_bedrock_function_parameter():
    # Test the conversion of kernel function parameter to bedrock function parameter
    parameter = KernelParameterMetadata(name="param1", description="Parameter 1", schema_data={"type": "string"}, is_required=True)
    result = kernel_function_parameter_to_bedrock_function_parameter(parameter)
    assert result == {
        "description": "Parameter 1",
        "type": "string",
        "required": True,
    }


def test_kernel_function_parameter_type_to_bedrock_function_parameter_type():
    # Test the conversion of kernel function parameter type to bedrock function parameter type
    schema_data = {"type": "string"}
    result = kernel_function_parameter_type_to_bedrock_function_parameter_type(schema_data)
    assert result == "string"


def test_kernel_function_parameter_type_to_bedrock_function_parameter_type_invalid():
    # Test the conversion of invalid kernel function parameter type to bedrock function parameter type
    schema_data = {"type": "invalid_type"}
    with pytest.raises(ValueError, match="Type invalid_type is not allowed in bedrock function parameter type. Allowed types are {'string', 'number', 'integer', 'boolean', 'array'}."):
        kernel_function_parameter_type_to_bedrock_function_parameter_type(schema_data)


def test_parse_return_control_payload():
    # Test the parsing of return control payload to function call contents
    return_control_payload = {
        "invocationId": "test_invocation_id",
        "invocationInputs": [
            {
                "functionInvocationInput": {
                    "function": "test_function",
                    "parameters": [
                        {"name": "param1", "value": "value1"},
                        {"name": "param2", "value": "value2"},
                    ],
                }
            }
        ],
    }
    result = parse_return_control_payload(return_control_payload)
    assert len(result) == 1
    assert result[0].id == "test_invocation_id"
    assert result[0].name == "test_function"
    assert result[0].arguments == {"param1": "value1", "param2": "value2"}


def test_parse_function_result_contents():
    # Test the parsing of function result contents to be returned to the agent
    function_result_contents = [
        FunctionResultContent(
            name="test_function",
            result="test_result",
            metadata={"functionInvocationInput": {"actionGroup": "test_action_group"}},
        )
    ]
    result = parse_function_result_contents(function_result_contents)
    assert len(result) == 1
    assert result[0]["functionResult"]["actionGroup"] == "test_action_group"
    assert result[0]["functionResult"]["function"] == "test_function"
    assert result[0]["functionResult"]["responseBody"]["TEXT"]["body"] == "test_result"
