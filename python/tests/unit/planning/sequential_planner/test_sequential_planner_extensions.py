# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.planning.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.planning.sequential_planner.sequential_planner_extensions import (
    SequentialPlannerFunctionViewExtension,
    SequentialPlannerKernelContextExtension,
)
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.plugin_collection import PluginCollection
from semantic_kernel.plugin_definition.read_only_plugin_collection_base import (
    ReadOnlyPluginCollectionBase,
)


async def _async_generator(query_result):
    yield query_result


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_no_functions_async():
    variables = ContextVariables()
    plugins = PluginCollection()

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
    memory.search_async.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext(variables, memory, plugins.read_only_plugin_collection)
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    memory.search_async.assert_not_called()


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions_async():
    variables = ContextVariables()

    function_mock = Mock(spec=KernelFunctionBase)
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

    plugins = Mock(spec=ReadOnlyPluginCollectionBase)
    plugins.get_function.return_value = function_mock
    plugins.get_functions_view.return_value = functions_view

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
    memory.search_async.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(variables=variables, memory=memory, plugin_collection=plugins)
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    assert len(result) == 2
    assert result[0] == function_view

    # Arrange update IncludedFunctions
    config.included_functions.append(["nativeFunctionName"])

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == function_view
    assert result[1] == native_function_view


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions_and_relevancy_async():
    # Arrange
    variables = ContextVariables()

    # Arrange FunctionView
    function_mock = Mock(spec=KernelFunctionBase)
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
    memory.search_async.return_value = _async_generator(memory_query_result)

    plugins = Mock(spec=ReadOnlyPluginCollectionBase)
    plugins.get_function.return_value = function_mock
    plugins.get_functions_view.return_value = functions_view
    plugins.read_only_plugin_collection = plugins

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(
        variables=variables,
        memory=memory,
        plugin_collection=plugins,
    )
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    assert len(result) == 1
    assert result[0] == function_view

    # Arrange update IncludedFunctions
    config.included_functions.append("nativeFunctionName")
    memory.search_async.return_value = _async_generator(memory_query_result)

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == function_view
    assert result[1] == native_function_view


@pytest.mark.asyncio
async def test_can_call_get_available_functions_async_with_default_relevancy_async():
    # Arrange
    variables = ContextVariables()
    plugins = PluginCollection()

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
    memory.search_async.return_value = async_enumerable

    # Arrange GetAvailableFunctionsAsync parameters
    context = KernelContext.model_construct(variables=variables, memory=memory, plugin_collection=plugins)
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelContextExtension.get_available_functions_async(
        context, config, semantic_query
    )

    # Assert
    assert result is not None
    memory.search_async.assert_called_once()
