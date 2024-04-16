# Copyright (c) Microsoft. All rights reserved.

from textwrap import dedent
from unittest.mock import Mock

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
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.planners.action_planner.action_planner_config import ActionPlannerConfig


@pytest.fixture
def plugins_input():
    return [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("today", "TimePlugin", "Get Today's date", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]


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


def test_throw_without_kernel():
    with pytest.raises(PlannerInvalidConfigurationError):
        ActionPlanner(None, None)


@pytest.fixture
def mock_kernel(plugins_input, kernel: Kernel):
    for name, plugin_name, description, is_prompt in plugins_input:
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

    return kernel


@pytest.mark.asyncio
async def test_plan_creation(kernel: Kernel):
    goal = "Translate Happy birthday to German."
    plan_str = dedent(
        """Here is a plan that can achieve the given task:\n\n{""plan"":\n{""rationale"":
        ""the list contains a function that allows to translate one language to another."",
        ""function"": ""WriterPlugin.Translate"",""parameters"": \n{""translate_from"":
        ""english"",""translate_to"": ""german"",""input"": ""Happy birthday""}\n}\n}\n\n
        This plan makes use of the Translate function in WriterPlugin to translate the message
        `Happy birthday` from english to german."""
    )

    mock_function = Mock(spec=KernelFunction)

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(
        kernel_function_metadata, FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={})
    )

    kernel.add_function("WriterPlugin", function=mock_function)

    planner = ActionPlanner(kernel, service_id="test")
    planner._planner_function = create_mock_function(
        KernelFunctionMetadata(
            name="ActionPlanner",
            description="Translate something",
            plugin_name=planner.RESTRICTED_PLUGIN_NAME,
            is_prompt=True,
            parameters=[],
        ),
        FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={}),
    )
    plan = await planner.create_plan(goal)

    assert plan is not None
    assert plan.description == mock_function.description
    assert "translate_from" in plan.state
    assert "translate_to" in plan.state
    assert "input" in plan.state


@pytest.mark.asyncio
async def test_no_parameter_plan_creation(kernel: Kernel):
    goal = "What date is it today?"
    plan_str = dedent(
        """Here is a plan that can achieve the given task:\n\n{""plan"":\n{""rationale"":
        ""the list contains a function that allows to get today's date."",
        ""function"": ""TimePlugin.today""\n}\n}\n\n
        This plan makes use of the today function in TimePlugin to get today's date."""
    )

    kernel_function_metadata = KernelFunctionMetadata(
        name="today",
        description="Get Today's date",
        plugin_name="TimePlugin",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(
        kernel_function_metadata, FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={})
    )

    kernel.add_function("TimePlugin", function=mock_function)

    planner = ActionPlanner(kernel, service_id="test")
    planner._planner_function = create_mock_function(
        KernelFunctionMetadata(
            name="ActionPlanner",
            description="Translate something",
            plugin_name=planner.RESTRICTED_PLUGIN_NAME,
            is_prompt=True,
            parameters=[],
        ),
        FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={}),
    )
    plan = await planner.create_plan(goal)

    assert plan is not None
    assert plan.parameters == {}
    assert plan.state == {}
    assert plan.description == mock_function.description


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
async def test_empty_goal_throw(kernel: Kernel):
    goal = ""
    mock_function = Mock(spec=KernelFunction)

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(
        kernel_function_metadata, FunctionResult(function=kernel_function_metadata, value="", metadata={})
    )
    kernel.add_function("WriterPlugin", mock_function)
    planner = ActionPlanner(kernel, service_id="test")

    with pytest.raises(PlannerInvalidGoalError):
        await planner.create_plan(goal)


@pytest.mark.asyncio
async def test_invalid_json_throw(kernel: Kernel):
    goal = "Translate Happy birthday to German."
    plan_str = '{"":{""function"": ""WriterPlugin.Translate""}}'

    kernel_function_metadata = KernelFunctionMetadata(
        name="Translate",
        plugin_name="WriterPlugin",
        description="Translate something",
        is_prompt=False,
        parameters=[],
    )
    mock_function = create_mock_function(
        kernel_function_metadata, FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={})
    )

    kernel.add_function("WriterPlugin", mock_function)
    planner = ActionPlanner(kernel, service_id="test")
    planner._planner_function = create_mock_function(
        KernelFunctionMetadata(
            name="ActionPlanner",
            description="Translate something",
            plugin_name=planner.RESTRICTED_PLUGIN_NAME,
            is_prompt=True,
            parameters=[],
        ),
        FunctionResult(function=kernel_function_metadata, value=plan_str, metadata={}),
    )

    with pytest.raises(PlannerInvalidPlanError):
        await planner.create_plan(goal)
