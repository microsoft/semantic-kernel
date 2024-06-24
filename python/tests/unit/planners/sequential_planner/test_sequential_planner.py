# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import PlannerException, PlannerInvalidGoalError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.planners.sequential_planner.sequential_planner import SequentialPlanner


def create_mock_function(kernel_function_metadata: KernelFunctionMetadata):
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.is_prompt = kernel_function_metadata.is_prompt
    mock_function.description = kernel_function_metadata.description
    mock_function.prompt_execution_settings = PromptExecutionSettings()
    return mock_function


@pytest.mark.asyncio
@pytest.mark.parametrize("goal", ["Write a poem or joke and send it in an e-mail to Kai."])
async def test_it_can_create_plan(goal):
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()

    memory = Mock(spec=SemanticTextMemoryBase)
    kernel.memory = memory

    input = [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]

    functions_list = []
    kernel.plugins = KernelPluginCollection()
    mock_functions = []
    for name, pluginName, description, is_prompt in input:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name=pluginName,
            description=description,
            parameters=[],
            is_prompt=is_prompt,
            is_asynchronous=True,
        )
        mock_function = create_mock_function(kernel_function_metadata)
        functions_list.append(kernel_function_metadata)
        mock_function.invoke.return_value = FunctionResult(
            function=kernel_function_metadata, value="MOCK FUNCTION CALLED", metadata={}
        )
        mock_functions.append(mock_function)

        if pluginName not in kernel.plugins.plugins:
            kernel.plugins.add(KernelPlugin(name=pluginName, description="Mock plugin"))
        kernel.plugins.add_functions_to_plugin([mock_function], pluginName)

    expected_functions = [x[0] for x in input]
    expected_plugins = [x[1] for x in input]

    plan_string = """
<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>"""

    mock_function_flow_function = Mock(spec=KernelFunction)
    mock_function_flow_function.invoke.return_value = FunctionResult(
        function=KernelFunctionMetadata(
            name="func", plugin_name="plugin", description="", parameters=[], is_prompt=False
        ),
        value=plan_string,
        metadata={},
    )
    kernel.create_function_from_prompt.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel, service_id="test")

    # Act
    plan = await planner.create_plan(goal)

    # Assert
    assert plan.description == goal
    assert any(step.name in expected_functions and step.plugin_name in expected_plugins for step in plan._steps)
    for expected_function in expected_functions:
        assert any(step.name == expected_function for step in plan._steps)
    for expectedPlugin in expected_plugins:
        assert any(step.plugin_name == expectedPlugin for step in plan._steps)


@pytest.mark.asyncio
async def test_empty_goal_throws():
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()
    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlannerInvalidGoalError):
        await planner.create_plan("")


@pytest.mark.asyncio
async def test_invalid_xml_throws():
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()
    memory = Mock(spec=SemanticTextMemoryBase)
    kernel.memory = memory
    plugins = Mock(spec=KernelPluginCollection)

    functions_list = []
    plugins.get_list_of_function_metadata.return_value = functions_list

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

    kernel.plugins = plugins
    kernel.create_function_from_prompt.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlannerException):
        await planner.create_plan("goal")
