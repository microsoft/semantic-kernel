# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import PlannerException, PlannerInvalidGoalError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.sequential_planner.sequential_planner import SequentialPlanner


def create_mock_function(
    kernel_function_metadata: KernelFunctionMetadata, return_value: FunctionResult
) -> KernelFunction:
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.is_prompt = kernel_function_metadata.is_prompt
    mock_function.description = kernel_function_metadata.description
    mock_function.prompt_execution_settings = PromptExecutionSettings()
    mock_function.invoke.return_value = return_value
    mock_function.function_copy.return_value = mock_function
    return mock_function


@pytest.mark.parametrize("goal", ["Write a poem or joke and send it in an e-mail to Kai."])
async def test_it_can_create_plan(goal, kernel: Kernel):
    # Arrange
    input = [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]

    for name, plugin_name, description, is_prompt in input:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name=plugin_name,
            description=description,
            parameters=[],
            is_prompt=is_prompt,
            is_asynchronous=True,
        )
        kernel.add_function(
            plugin_name,
            function=create_mock_function(
                kernel_function_metadata,
                FunctionResult(
                    function=kernel_function_metadata, value="MOCK FUNCTION CALLED", metadata={"arguments": {}}
                ),
            ),
        )

    expected_functions = [x[0] for x in input]
    expected_plugins = [x[1] for x in input]

    plan_string = """
<plan>
    <function.SummarizePlugin-Summarize/>
    <function.WriterPlugin-Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email-GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email-SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>"""

    mock_function_flow_function = Mock(spec=KernelFunction)
    mock_function_flow_function.invoke.return_value = FunctionResult(
        function=KernelFunctionMetadata(
            name="func", plugin_name="plugin", description="", parameters=[], is_prompt=False
        ),
        value=plan_string,
        metadata={},
    )

    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function
    # Act
    plan = await planner.create_plan(goal)

    # Assert
    assert plan.description == goal
    assert any(step.name in expected_functions and step.plugin_name in expected_plugins for step in plan._steps)
    for expected_function in expected_functions:
        assert any(step.name == expected_function for step in plan._steps)
    for expectedPlugin in expected_plugins:
        assert any(step.plugin_name == expectedPlugin for step in plan._steps)


async def test_empty_goal_throws(kernel: Kernel):
    # Arrange
    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlannerInvalidGoalError):
        await planner.create_plan("")


async def test_invalid_xml_throws(kernel: Kernel):
    # Arrange

    plan_string = "<plan>notvalid<</plan>"
    function_result = FunctionResult(
        function=KernelFunctionMetadata(
            name="func", plugin_name="plugin", description="", parameters=[], is_prompt=False
        ),
        value=plan_string,
        metadata={},
    )

    mock_function_flow_function = Mock(spec=KernelFunction)
    mock_function_flow_function.invoke.return_value = function_result

    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function

    # Act & Assert
    with pytest.raises(PlannerException):
        await planner.create_plan("goal")
