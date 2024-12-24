# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import Mock

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.sequential_planner.sequential_planner_config import SequentialPlannerConfig
from semantic_kernel.planners.sequential_planner.sequential_planner_extensions import SequentialPlannerKernelExtension


async def _async_generator(query_result):
    yield query_result


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


async def test_can_call_get_available_functions_with_no_functions(kernel: Kernel):
    arguments = KernelArguments()

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig()
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None


async def test_can_call_get_available_functions_with_functions(kernel: Kernel):
    arguments = KernelArguments()
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
    kernel.add_function("pluginName", create_mock_function(kernel_function_metadata, None))
    kernel.add_function("pluginName", create_mock_function(native_kernel_function_metadata, None))

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


async def test_can_call_get_available_functions_with_default_relevancy(kernel: Kernel):
    # Arrange
    arguments = KernelArguments()

    # Arrange GetAvailableFunctionsAsync parameters
    config = SequentialPlannerConfig(relevancy_threshold=0.78)
    semantic_query = "test"

    # Act
    result = await SequentialPlannerKernelExtension.get_available_functions(kernel, arguments, config, semantic_query)

    # Assert
    assert result is not None
