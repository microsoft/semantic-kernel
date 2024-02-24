# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.planners.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import (
    SequentialPlannerFunctionViewExtension,
    SequentialPlannerKernelExtension,
)


async def _async_generator(query_result):
    yield query_result


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_no_functions():
    arguments = KernelArguments()
    kernel = Kernel()

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
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_not_called()


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions():
    arguments = KernelArguments()
    kernel = Kernel()
    functions_list = []
    kernel_function_metadata = KernelFunctionMetadata(
        name="functionName",
        plugin_name="pluginName",
        description="description",
        parameters=[],
        is_prompt=True,
        is_asynchronous=False,
    )
    native_kernel_function_metadata = KernelFunctionMetadata(
        name="nativeFunctionName",
        plugin_name="pluginName",
        description="description",
        parameters=[],
        is_prompt=False,
        is_asynchronous=False,
    )
    functions_list.append(kernel_function_metadata)
    functions_list.append(native_kernel_function_metadata)

    mock_plugins = Mock(spec=KernelPluginCollection)
    mock_plugins.get_list_of_function_metadata.return_value = functions_list

    kernel.plugins = mock_plugins

    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id=SequentialPlannerFunctionViewExtension.to_fully_qualified_name(kernel_function_metadata),
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
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2
    assert result[0] == kernel_function_metadata

    # Arrange update IncludedFunctions
    config.included_functions.append(["nativeFunctionName"])

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == kernel_function_metadata
    assert result[1] == native_kernel_function_metadata


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions_and_relevancy():
    # Arrange FunctionView
    functions_list = []
    kernel_function_metadata = KernelFunctionMetadata(
        name="functionName",
        plugin_name="pluginName",
        description="description",
        parameters=[],
        is_prompt=True,
        is_asynchronous=False,
    )
    native_kernel_function_metadata = KernelFunctionMetadata(
        name="nativeFunctionName",
        plugin_name="pluginName",
        description="description",
        parameters=[],
        is_prompt=False,
        is_asynchronous=False,
    )
    functions_list.append(kernel_function_metadata)
    functions_list.append(native_kernel_function_metadata)

    # Arrange Mock Memory and Result
    memory_query_result = MemoryQueryResult(
        is_reference=False,
        id=SequentialPlannerFunctionViewExtension.to_fully_qualified_name(kernel_function_metadata),
        text="text",
        description="description",
        external_source_name="sourceName",
        additional_metadata="value",
        relevance=0.8,
        embedding=None,
    )
    memory = Mock(spec=SemanticTextMemoryBase)
    memory.search.return_value = [memory_query_result]

    mock_plugins = Mock(spec=KernelPluginCollection)
    mock_plugins.get_list_of_function_metadata.return_value = functions_list

    # Arrange GetAvailableFunctionsAsync parameters
    kernel = Kernel()
    kernel.plugins = mock_plugins
    kernel.memory = memory
    arguments = KernelArguments()
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 1
    assert result[0] == kernel_function_metadata

    # Arrange update IncludedFunctions
    config.included_functions.append("nativeFunctionName")
    memory.search.return_value = [memory_query_result]

    arguments = KernelArguments()
    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == kernel_function_metadata
    assert result[1] == native_kernel_function_metadata


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_default_relevancy():
    # Arrange
    plugins = KernelPluginCollection()
    kernel = Kernel()
    kernel.plugins = plugins
    arguments = KernelArguments()

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
    memory = Mock(spec=SemanticTextMemoryBase)
    memory.search.return_value = [memory_query_result]
    kernel.memory = memory

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_called_once()
