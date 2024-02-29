# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import (
    SequentialPlannerKernelExtension,
)


async def _async_generator(query_result):
    yield query_result


@pytest.mark.asyncio
async def test_can_call_get_available_functions_with_no_functions():
    arguments = KernelArguments()
    kernel = Kernel()

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None


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
async def test_can_call_get_available_functions_with_default_relevancy():
    # Arrange
    plugins = KernelPluginCollection()
    kernel = Kernel()
    kernel.plugins = plugins
    arguments = KernelArguments()

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
