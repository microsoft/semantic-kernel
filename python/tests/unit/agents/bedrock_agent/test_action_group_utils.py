# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.agents.bedrock.action_group_utils import (
    BEDROCK_FUNCTION_ALLOWED_PARAMETER_TYPES,
    kernel_function_parameter_type_to_bedrock_function_parameter_type,
    kernel_function_to_bedrock_function_schema,
    parse_function_result_contents,
    parse_return_control_payload,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.kernel import Kernel


def test_kernel_function_to_bedrock_function_schema(kernel_with_function: Kernel):
    # Test the conversion of kernel function to bedrock function schema
    function_choice_behavior = FunctionChoiceBehavior.Auto()
    function_choice_configuration = function_choice_behavior.get_config(kernel_with_function)
    result = kernel_function_to_bedrock_function_schema(function_choice_configuration)
    assert result == {
        "functions": [
            {
                "name": "test_plugin-getLightStatus",
                "parameters": {
                    "arg1": {
                        "type": "string",
                        "required": True,
                    }
                },
                "requireConfirmation": "DISABLED",
            }
        ]
    }


def test_kernel_function_parameter_type_to_bedrock_function_parameter_type():
    # Test the conversion of kernel function parameter type to bedrock function parameter type
    schema_data = {"type": "string"}
    result = kernel_function_parameter_type_to_bedrock_function_parameter_type(schema_data)
    assert result == "string"


def test_kernel_function_parameter_type_to_bedrock_function_parameter_type_invalid():
    # Test the conversion of invalid kernel function parameter type to bedrock function parameter type
    schema_data = {"type": "invalid_type"}
    with pytest.raises(
        ValueError,
        match="Type invalid_type is not allowed in bedrock function parameter type. "
        f"Allowed types are {BEDROCK_FUNCTION_ALLOWED_PARAMETER_TYPES}.",
    ):
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
            id="test_id",
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
