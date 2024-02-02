# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.planning.planning_exception import PlanningException
from semantic_kernel.planning.sequential_planner.sequential_planner import (
    SequentialPlanner,
)
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin
from semantic_kernel.plugin_definition.kernel_plugin_collection import (
    KernelPluginCollection,
)


def create_mock_function(function_view: FunctionView):
    mock_function = Mock(spec=KernelFunctionBase)
    mock_function.describe.return_value = function_view
    mock_function.name = function_view.name
    mock_function.plugin_name = function_view.plugin_name
    return mock_function


@pytest.mark.asyncio
@pytest.mark.parametrize("goal", ["Write a poem or joke and send it in an e-mail to Kai."])
async def test_it_can_create_plan(goal):
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()

    memory = Mock(spec=SemanticTextMemoryBase)

    input = [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterPlugin", "Translate something", True),
        ("Summarize", "SummarizePlugin", "Summarize something", True),
    ]

    functionsView = FunctionsView()
    plugins = KernelPluginCollection()
    mock_functions = []
    for name, pluginName, description, isSemantic in input:
        function_view = FunctionView(name, pluginName, description, [], isSemantic, True)
        mock_function = create_mock_function(function_view)
        functionsView.add_function(function_view)

        context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugins=plugins)
        context.variables.update("MOCK FUNCTION CALLED")
        mock_function.invoke.return_value = context
        mock_functions.append(mock_function)

        if pluginName not in plugins.plugins:
            plugins.add(KernelPlugin(name=pluginName, description="Mock plugin"))
        plugins.add_functions_to_plugin([mock_function], pluginName)

    expected_functions = [x[0] for x in input]
    expected_plugins = [x[1] for x in input]

    context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugins=plugins)
    return_context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugins=plugins)
    plan_string = """
<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>"""

    return_context.variables.update(plan_string)

    mock_function_flow_function = Mock(spec=KernelFunctionBase)
    mock_function_flow_function.invoke.return_value = return_context

    kernel.plugins = plugins
    kernel.create_new_context.return_value = context
    kernel.register_semantic_function.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel)

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
    planner = SequentialPlanner(kernel)

    # Act & Assert
    with pytest.raises(PlanningException):
        await planner.create_plan("")


@pytest.mark.asyncio
async def test_invalid_xml_throws():
    # Arrange
    kernel = Mock(spec=Kernel)
    kernel.prompt_template_engine = Mock()
    memory = Mock(spec=SemanticTextMemoryBase)
    plugins = Mock(spec=KernelPluginCollection)

    functionsView = FunctionsView()
    plugins.get_functions_view.return_value = functionsView

    plan_string = "<plan>notvalid<</plan>"
    return_context = KernelContext.model_construct(
        variables=ContextVariables(plan_string),
        memory=memory,
        plugins=plugins,
    )

    context = KernelContext.model_construct(variables=ContextVariables(), memory=memory, plugins=plugins)

    mock_function_flow_function = Mock(spec=KernelFunctionBase)
    mock_function_flow_function.invoke.return_value = return_context

    kernel.plugins = plugins
    kernel.create_new_context.return_value = context
    kernel.register_semantic_function.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel)

    # Act & Assert
    with pytest.raises(PlanningException):
        await planner.create_plan("goal")
