# Copyright (c) Microsoft. All rights reserved.

from textwrap import dedent
from unittest.mock import MagicMock, Mock

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import (
    PlannerInvalidConfigurationError,
    PlannerInvalidGoalError,
    PlannerInvalidPlanError,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.planners.action_planner.action_planner_config import (
    ActionPlannerConfig,
)
from semantic_kernel.planners.planning_exception import PlanningException
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.planners.action_planner.action_planner_config import ActionPlannerConfig


def create_mock_function(kernel_function_metadata: KernelFunctionMetadata) -> Mock(spec=KernelFunction):
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.is_prompt = kernel_function_metadata.is_prompt
    mock_function.description = kernel_function_metadata.description
    mock_function.prompt_execution_settings = PromptExecutionSettings()
    return mock_function


def test_throw_without_kernel():
    with pytest.raises(PlanningException):
    with pytest.raises(PlannerInvalidConfigurationError):
        ActionPlanner(None, None)


@pytest.fixture
def mock_kernel(plugins_input):
    kernel = Mock(spec=Kernel)
    plugins = MagicMock(spec=KernelPluginCollection)
    functions_list = []

    mock_plugins = {}

    for name, plugin_name, description, is_prompt in plugins_input:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name=plugin_name,
            description=description,
            parameters=[],
            is_prompt=is_prompt,
            is_asynchronous=True,
        )
        mock_function = create_mock_function(kernel_function_metadata)
        functions_list.append(kernel_function_metadata)

        if plugin_name not in mock_plugins:
            mock_plugins[plugin_name] = {}
        mock_plugins[plugin_name][name] = mock_function

        mock_function.invoke.return_value = FunctionResult(
            function=kernel_function_metadata, value="MOCK FUNCTION CALLED", metadata={"arguments": {}}
        )

    plugins.__getitem__.side_effect = lambda plugin_name: MagicMock(__getitem__=mock_plugins[plugin_name].__getitem__)

    kernel.plugins = plugins
    kernel.plugins.get_list_of_function_metadata.return_value = functions_list
    return kernel


@pytest.mark.asyncio
async def test_plan_creation():
    goal = "Translate Happy birthday to German."
    plan_str = dedent(
        """Here is a plan that can achieve the given task:\n\n{""plan"":\n{""rationale"":
        ""the list contains a function that allows to translate one language to another."",
        ""function"": ""WriterPlugin.Translate"",""parameters"": \n{""translate_from"":
        ""english"",""translate_to"": ""german"",""input"": ""Happy birthday""}\n}\n}\n\n
        This plan makes use of the Translate function in WriterPlugin to translate the message
        `Happy birthday` from english to german."""
    )

    kernel = Mock(spec=Kernel)
    mock_function = Mock(spec=KernelFunction)
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = KernelPluginCollection()
    kernel.plugins = plugins
    kernel.register_memory(memory)
    plugins = KernelPluginCollection()
    kernel.plugins = plugins

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(kernel_function_metadata)

    kernel.plugins.add(plugin=KernelPlugin(name=kernel_function_metadata.plugin_name, functions=[mock_function]))

    function_result = FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={})
    mock_function.invoke.return_value = function_result

    kernel.create_function_from_prompt.return_value = mock_function

    planner = ActionPlanner(kernel, service_id="test")
    plan = await planner.create_plan(goal)

    assert plan is not None
    assert plan.description == mock_function.description
    assert "translate_from" in plan.state
    assert "translate_to" in plan.state
    assert "input" in plan.state


@pytest.fixture
def plugins_input():
    return [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]


def test_available_functions(plugins_input, mock_kernel):
    goal = "Translate Happy birthday to German."

    planner = ActionPlanner(mock_kernel, service_id="test")
    result = planner.list_of_functions(goal=goal)

    expected_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input[1:]]

    assert all(plugin in result for plugin in expected_plugins)


def test_exclude_plugins(plugins_input, mock_kernel):
    goal = "Translate Happy birthday to German."

    # Exclude the first and second in plugins_input
    excluded_plugin_name = "email"

    planner_config = ActionPlannerConfig(excluded_plugins=[excluded_plugin_name])
    planner = ActionPlanner(mock_kernel, service_id="test", config=planner_config)
    result = planner.list_of_functions(goal=goal)

    all_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input]
    excluded_plugins = all_plugins[:2]
    expected_plugins = all_plugins[2:]

    assert all(plugin in result for plugin in expected_plugins)
    assert all(plugin not in result for plugin in excluded_plugins)


def test_exclude_functions(plugins_input, mock_kernel):
    goal = "Translate Happy birthday to German."

    excluded_function_name = "SendEmail"

    planner_config = ActionPlannerConfig(excluded_functions=[excluded_function_name])
    planner = ActionPlanner(mock_kernel, service_id="test", config=planner_config)
    result = planner.list_of_functions(goal=goal)

    all_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input]
    excluded_plugins = all_plugins[:1]
    expected_plugins = all_plugins[1:]

    assert all(plugin in result for plugin in expected_plugins)
    assert all(plugin not in result for plugin in excluded_plugins)


@pytest.mark.asyncio
async def test_empty_goal_throw():
    goal = ""

    kernel = Mock(spec=Kernel)
    mock_function = Mock(spec=KernelFunction)
    plugins = MagicMock(spec=KernelPluginCollection)
    kernel.plugins = plugins

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(kernel_function_metadata)
    kernel.plugins.__getitem__.return_value = MagicMock(__getitem__=MagicMock(return_value=mock_function))

    planner = ActionPlanner(kernel, service_id="test")

    with pytest.raises(PlanningException):
    with pytest.raises(PlannerInvalidGoalError):
        await planner.create_plan(goal)


@pytest.mark.asyncio
async def test_invalid_json_throw():
    goal = "Translate Happy birthday to German."
    plan_str = '{"":{""function"": ""WriterPlugin.Translate""}}'

    kernel = Mock(spec=Kernel)
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = MagicMock(spec=KernelPluginCollection)
    kernel.plugins = plugins
    kernel.register_memory(memory)
    plugins = MagicMock(spec=KernelPluginCollection)
    kernel.plugins = plugins

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        plugin_name="WriterPlugin",
        description="Translate something",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(kernel_function_metadata)

    plugins.__getitem__.return_value = MagicMock(__getitem__=MagicMock(return_value=mock_function))

    function_result = FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={})
    mock_function.invoke.return_value = function_result

    kernel.create_function_from_prompt.return_value = mock_function

    planner = ActionPlanner(kernel, service_id="test")

    with pytest.raises(PlanningException):
    with pytest.raises(PlannerInvalidPlanError):
        await planner.create_plan(goal)
