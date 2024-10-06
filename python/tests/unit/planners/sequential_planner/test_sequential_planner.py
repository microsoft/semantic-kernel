# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.exceptions import PlannerException, PlannerInvalidGoalError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.planners.planning_exception import PlanningException
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.planners.sequential_planner.sequential_planner import (
    SequentialPlanner,
)


<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def create_mock_function(
    kernel_function_metadata: KernelFunctionMetadata, return_value: FunctionResult
) -> KernelFunction:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
def create_mock_function(
    kernel_function_metadata: KernelFunctionMetadata, return_value: FunctionResult
) -> KernelFunction:
=======
<<<<<<< HEAD
def create_mock_function(
    kernel_function_metadata: KernelFunctionMetadata, return_value: FunctionResult
) -> KernelFunction:
=======
def create_mock_function(kernel_function_metadata: KernelFunctionMetadata):
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.is_prompt = kernel_function_metadata.is_prompt
    mock_function.description = kernel_function_metadata.description
    mock_function.prompt_execution_settings = PromptExecutionSettings()
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    mock_function.invoke.return_value = return_value
    mock_function.function_copy.return_value = mock_function
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    mock_function.invoke.return_value = return_value
    mock_function.function_copy.return_value = mock_function
=======
<<<<<<< HEAD
    mock_function.invoke.return_value = return_value
    mock_function.function_copy.return_value = mock_function
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return mock_function


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@pytest.mark.parametrize(
    "goal", ["Write a poem or joke and send it in an e-mail to Kai."]
)
async def test_it_can_create_plan(goal, kernel: Kernel):
    # Arrange
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
@pytest.mark.parametrize("goal", ["Write a poem or joke and send it in an e-mail to Kai."])
async def test_it_can_create_plan(goal):
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()

    memory = Mock(spec=SemanticTextMemoryBase)
    kernel.memory = memory

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    input = [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for name, plugin_name, description, is_prompt in input:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name=plugin_name,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    functions_list = []
    kernel.plugins = KernelPluginCollection()
    mock_functions = []
    for name, pluginName, description, is_prompt in input:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name=pluginName,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            description=description,
            parameters=[],
            is_prompt=is_prompt,
            is_asynchronous=True,
        )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        kernel.add_function(
            plugin_name,
            function=create_mock_function(
                kernel_function_metadata,
                FunctionResult(
                    function=kernel_function_metadata,
                    value="MOCK FUNCTION CALLED",
                    metadata={"arguments": {}},
                ),
            ),
        )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
        mock_function = create_mock_function(kernel_function_metadata)
        functions_list.append(kernel_function_metadata)
        mock_function.invoke.return_value = FunctionResult(
            function=kernel_function_metadata, value="MOCK FUNCTION CALLED", metadata={}
        )
        mock_functions.append(mock_function)

        if pluginName not in kernel.plugins.plugins:
            kernel.plugins.add(KernelPlugin(name=pluginName, description="Mock plugin"))
        kernel.plugins.add_functions_to_plugin([mock_function], pluginName)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    expected_functions = [x[0] for x in input]
    expected_plugins = [x[1] for x in input]

    plan_string = """
<plan>
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    <function.SummarizePlugin-Summarize/>
    <function.WriterPlugin-Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email-GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email-SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
</plan>"""

    mock_function_flow_function = Mock(spec=KernelFunction)
    mock_function_flow_function.invoke.return_value = FunctionResult(
        function=KernelFunctionMetadata(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            name="func",
            plugin_name="plugin",
            description="",
            parameters=[],
            is_prompt=False,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
            name="func", plugin_name="plugin", description="", parameters=[], is_prompt=False
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        ),
        value=plan_string,
        metadata={},
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function
=======
<<<<<<< HEAD

    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function
=======
    kernel.create_function_from_prompt.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel, service_id="test")

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    # Act
    plan = await planner.create_plan(goal)

    # Assert
    assert plan.description == goal
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert any(
        step.name in expected_functions and step.plugin_name in expected_plugins
        for step in plan._steps
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    assert any(step.name in expected_functions and step.plugin_name in expected_plugins for step in plan._steps)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    for expected_function in expected_functions:
        assert any(step.name == expected_function for step in plan._steps)
    for expectedPlugin in expected_plugins:
        assert any(step.plugin_name == expectedPlugin for step in plan._steps)


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_empty_goal_throws(kernel: Kernel):
    # Arrange
    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlannerInvalidGoalError):
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_empty_goal_throws():
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()
    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlanningException):
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await planner.create_plan("")


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
async def test_invalid_xml_throws(kernel: Kernel):
    # Arrange
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
async def test_invalid_xml_throws(kernel: Kernel):
    # Arrange
=======
<<<<<<< HEAD
async def test_invalid_xml_throws(kernel: Kernel):
    # Arrange
=======
async def test_invalid_xml_throws():
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()
    memory = Mock(spec=SemanticTextMemoryBase)
    kernel.memory = memory
    plugins = Mock(spec=KernelPluginCollection)

    functions_list = []
    plugins.get_list_of_function_metadata.return_value = functions_list
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan_string = "<plan>notvalid<</plan>"
    function_result = FunctionResult(
        function=KernelFunctionMetadata(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            name="func",
            plugin_name="plugin",
            description="",
            parameters=[],
            is_prompt=False,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
            name="func", plugin_name="plugin", description="", parameters=[], is_prompt=False
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        ),
        value=plan_string,
        metadata={},
    )

    mock_function_flow_function = Mock(spec=KernelFunction)
    mock_function_flow_function.invoke.return_value = function_result

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    planner = SequentialPlanner(kernel, service_id="test")
    planner._function_flow_function = mock_function_flow_function

    # Act & Assert
    with pytest.raises(PlannerException):
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    kernel.plugins = plugins
    kernel.create_function_from_prompt.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel, service_id="test")

    # Act & Assert
    with pytest.raises(PlanningException):
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await planner.create_plan("goal")
