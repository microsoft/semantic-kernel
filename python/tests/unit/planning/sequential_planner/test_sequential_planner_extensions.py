# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.planning.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.planning.sequential_planner.sequential_planner_extensions import (
    SequentialPlannerFunctionViewExtension,
    SequentialPlannerKernelContextExtension,
)
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.kernel_plugin_collection import (
    KernelPluginCollection,
)


async def _async_generator(query_result):
    yield query_result


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_no_functions():
    variables = ContextVariables()
    plugins = KernelPluginCollection()

    memory = Mock(spec=SemanticTextMemoryBase)
    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id="id",
        text="text",
        description="description",
        external_source_name="sourceName",
        additional_metadata="value",
        relevance=0.8,
        embedding=None,
    )

    async_enumerable = _async_generator(memory_query_result)
    memory.search.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext(variables=variables, memory=memory, plugins=plugins)
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_not_called()


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions():
    variables = ContextVariables()

    functions_view = FunctionsView()
    function_view = FunctionView(
        "functionName",
        "pluginName",
        "description",
        [],
        is_semantic=True,
        is_asynchronous=False,
    )
    native_function_view = FunctionView(
        "nativeFunctionName",
        "pluginName",
        "description",
        [],
        is_semantic=False,
        is_asynchronous=False,
    )
    functions_view.add_function(function_view)
    functions_view.add_function(native_function_view)

    mock_plugins = Mock(spec=KernelPluginCollection)
    mock_plugins.get_functions_view.return_value = functions_view

    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id=SequentialPlannerFunctionViewExtension.to_fully_qualified_name(function_view),
        text="text",
        description="description",
        external_source_name="sourceName",
        additional_metadata="value",
        relevance=0.8,
        embedding=None,
    )

    async_enumerable = _async_generator(memory_query_result)
    memory = Mock(spec=SemanticTextMemoryBase)
    memory.search.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(variables=variables, memory=memory, plugins=mock_plugins)
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2
    assert result[0] == function_view

    # Arrange update IncludedFunctions
    config.included_functions.append(["nativeFunctionName"])

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == function_view
    assert result[1] == native_function_view


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions_and_relevancy():
    # Arrange
    variables = ContextVariables()

    # Arrange FunctionView
    functions_view = FunctionsView()
    function_view = FunctionView(
        "functionName",
        "pluginName",
        "description",
        [],
        is_semantic=True,
        is_asynchronous=False,
    )
    native_function_view = FunctionView(
        "nativeFunctionName",
        "pluginName",
        "description",
        [],
        is_semantic=False,
        is_asynchronous=False,
    )
    functions_view.add_function(function_view)
    functions_view.add_function(native_function_view)

    # Arrange Mock Memory and Result
    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id=SequentialPlannerFunctionViewExtension.to_fully_qualified_name(function_view),
        text="text",
        description="description",
        external_source_name="sourceName",
        additional_metadata="value",
        relevance=0.8,
        embedding=None,
    )
    memory = Mock(spec=SemanticTextMemoryBase)
    memory.search.return_value = _async_generator(memory_query_result)

    mock_plugins = Mock(spec=KernelPluginCollection)
    mock_plugins.get_functions_view.return_value = functions_view

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(
        variables=variables,
        memory=memory,
        plugins=mock_plugins,
    )
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 1
    assert result[0] == function_view

    # Arrange update IncludedFunctions
    config.included_functions.append("nativeFunctionName")
    memory.search.return_value = _async_generator(memory_query_result)

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == function_view
    assert result[1] == native_function_view


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_default_relevancy():
    # Arrange
    variables = ContextVariables()
    plugins = KernelPluginCollection()

    # Arrange Mock Memory and Result
    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id="id",
        text="text",
        description="description",
        external_source_name="sourceName",
        additional_metadata="value",
        relevance=0.8,
        embedding=None,
    )
    async_enumerable = _async_generator(memory_query_result)
    memory = Mock(spec=SemanticTextMemoryBase)
    memory.search.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(variables=variables, memory=memory, plugins=plugins)
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions(context, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_called_once()
