from textwrap import dedent
from unittest.mock import Mock

import pytest

from semantic_kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.planning import ActionPlanner
from semantic_kernel.planning.action_planner.action_planner_config import (
    ActionPlannerConfig,
)
from semantic_kernel.planning.planning_exception import PlanningException
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.plugin_collection_base import (
    PluginCollectionBase,
)


def create_mock_function(function_view: FunctionView) -> Mock(spec=KernelFunctionBase):
    mock_function = Mock(spec=KernelFunctionBase)
    mock_function.describe.return_value = function_view
    mock_function.name = function_view.name
    mock_function.plugin_name = function_view.plugin_name
    mock_function.description = function_view.description
    return mock_function


def test_throw_without_kernel():
    with pytest.raises(PlanningException):
        ActionPlanner(None)


def test_throw_without_completion_service():
    kernel = Kernel()

    with pytest.raises(ValueError):
        ActionPlanner(kernel)


@pytest.mark.asyncio
async def test_plan_creation_async():
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
    mock_function = Mock(spec=KernelFunctionBase)
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = Mock(spec=PluginCollectionBase)

    function_view = FunctionView(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_semantic=False,
        parameters=[],
    )
    mock_function = create_mock_function(function_view)
    plugins.get_function.return_value = mock_function

    context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugin_collection=plugins)
    return_context = KernelContext.model_construct(
        variables=ContextVariables(), memory=memory, plugin_collection=plugins
    )

    return_context.variables.update(plan_str)

    mock_function.invoke_async.return_value = return_context

    kernel.create_semantic_function.return_value = mock_function
    kernel.create_new_context.return_value = context

    planner = ActionPlanner(kernel)
    plan = await planner.create_plan_async(goal)

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


@pytest.fixture
def mock_context(plugins_input):
    memory = Mock(spec=Kernel)
    context = Mock(spec=KernelContext)

    functionsView = FunctionsView()
    plugins = Mock(spec=PluginCollectionBase)
    mock_functions = []
    for name, pluginName, description, isSemantic in plugins_input:
        function_view = FunctionView(name, pluginName, description, [], isSemantic, True)
        mock_function = create_mock_function(function_view)
        functionsView.add_function(function_view)

        _context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugin_collection=plugins)
        _context.variables.update("MOCK FUNCTION CALLED")
        mock_function.invoke_async.return_value = _context
        mock_functions.append(mock_function)

    plugins.get_function.side_effect = lambda plugin_name, function_name: next(
        (func for func in mock_functions if func.plugin_name == plugin_name and func.name == function_name),
        None,
    )
    plugins.get_functions_view.return_value = functionsView
    context.plugins.return_value = plugins
    context.plugins.get_functions_view.return_value = functionsView

    return context


def test_available_functions(plugins_input, mock_context):
    goal = "Translate Happy birthday to German."
    kernel = Mock(spec=Kernel)

    planner = ActionPlanner(kernel)
    result = planner.list_of_functions(goal=goal, context=mock_context)

    expected_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input[1:]]

    assert all(plugin in result for plugin in expected_plugins)


def test_exclude_plugins(plugins_input, mock_context):
    goal = "Translate Happy birthday to German."
    kernel = Mock(spec=Kernel)

    # Exclude the first and second in plugins_input
    excluded_plugin_name = "email"

    planner_config = ActionPlannerConfig(excluded_plugins=[excluded_plugin_name])
    planner = ActionPlanner(kernel, config=planner_config)
    result = planner.list_of_functions(goal=goal, context=mock_context)

    all_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input]
    excluded_plugins = all_plugins[:2]
    expected_plugins = all_plugins[2:]

    assert all(plugin in result for plugin in expected_plugins)
    assert all(plugin not in result for plugin in excluded_plugins)


def test_exclude_functions(plugins_input, mock_context):
    goal = "Translate Happy birthday to German."
    kernel = Mock(spec=Kernel)

    excluded_function_name = "SendEmail"

    planner_config = ActionPlannerConfig(excluded_functions=[excluded_function_name])
    planner = ActionPlanner(kernel, config=planner_config)
    result = planner.list_of_functions(goal=goal, context=mock_context)

    all_plugins = [f"{val[1]}.{val[0]}" for val in plugins_input]
    excluded_plugins = all_plugins[:1]
    expected_plugins = all_plugins[1:]

    assert all(plugin in result for plugin in expected_plugins)
    assert all(plugin not in result for plugin in excluded_plugins)


@pytest.mark.asyncio
async def test_invalid_json_throw_async():
    goal = "Translate Happy birthday to German."
    plan_str = '{"":{""function"": ""WriterPlugin.Translate""}}'

    kernel = Mock(spec=Kernel)
    mock_function = Mock(spec=KernelFunctionBase)
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = Mock(spec=PluginCollectionBase)

    function_view = FunctionView(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_semantic=False,
        parameters=[],
    )
    mock_function = create_mock_function(function_view)
    plugins.get_function.return_value = mock_function

    context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugin_collection=plugins)
    return_context = KernelContext.model_construct(
        variables=ContextVariables(), memory=memory, plugin_collection=plugins
    )

    return_context.variables.update(plan_str)

    mock_function.invoke_async.return_value = return_context

    kernel.create_semantic_function.return_value = mock_function
    kernel.create_new_context.return_value = context

    planner = ActionPlanner(kernel)

    with pytest.raises(PlanningException):
        await planner.create_plan_async(goal)


@pytest.mark.asyncio
async def test_empty_goal_throw_async():
    goal = ""

    kernel = Mock(spec=Kernel)
    mock_function = Mock(spec=KernelFunctionBase)
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = Mock(spec=PluginCollectionBase)

    function_view = FunctionView(
        name="Translate",
        description="Translate something",
        plugin_name="WriterPlugin",
        is_semantic=False,
        parameters=[],
    )
    mock_function = create_mock_function(function_view)
    plugins.get_function.return_value = mock_function

    context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugin_collection=plugins)
    return_context = KernelContext.model_construct(
        variables=ContextVariables(), memory=memory, plugin_collection=plugins
    )
    mock_function.invoke_async.return_value = return_context

    kernel.create_semantic_function.return_value = mock_function
    kernel.create_new_context.return_value = context

    planner = ActionPlanner(kernel)

    with pytest.raises(PlanningException):
        await planner.create_plan_async(goal)
