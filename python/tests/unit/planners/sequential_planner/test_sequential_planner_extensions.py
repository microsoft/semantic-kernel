# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======

=======
>>>>>>> Stashed changes
<<<<<<< HEAD

=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from unittest.mock import Mock

import pytest

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.planners.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import (
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    SequentialPlannerFunctionViewExtension,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    SequentialPlannerKernelExtension,
)


async def _async_generator(query_result):
    yield query_result


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
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


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_no_functions(kernel: Kernel):
    arguments = KernelArguments()
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )

    # Assert
    assert result is not None


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions(kernel: Kernel):
    arguments = KernelArguments()
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_not_called()


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_functions():
    arguments = KernelArguments()
    kernel = Kernel()
    functions_list = []
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    kernel.add_function(
        "pluginName", create_mock_function(kernel_function_metadata, None)
    )
    kernel.add_function(
        "pluginName", create_mock_function(native_kernel_function_metadata, None)
    )

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
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

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    # Assert
    assert result is not None
    assert len(result) == 2
    assert result[0] == kernel_function_metadata

    # Arrange update IncludedFunctions
    config.included_functions.append(["nativeFunctionName"])

    # Act
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )
=======
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == kernel_function_metadata
    assert result[1] == native_kernel_function_metadata


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    # Assert
    assert result is not None
    assert len(result) == 2  # IncludedFunctions should be added to the result
    assert result[0] == kernel_function_metadata
    assert result[1] == native_kernel_function_metadata


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
async def test_can_call_get_available_functions_with_default_relevancy(kernel: Kernel):
    # Arrange
    arguments = KernelArguments()

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
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

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(
        kernel, arguments, config, semantic_query
    )

    # Assert
    assert result is not None
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
    memory.search.assert_called_once()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
