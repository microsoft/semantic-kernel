# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel import Kernel
from semantic_kernel.events.function_invoked_event_args import FunctionInvokedEventArgs
from semantic_kernel.events.function_invoking_event_args import FunctionInvokingEventArgs
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin


def create_mock_function(name) -> KernelFunction:
    kernel_function_metadata = KernelFunctionMetadata(
        name=name,
        plugin_name="SummarizePlugin",
        description="Summarize an input",
        parameters=[],
        is_prompt=True,
        is_asynchronous=True,
    )
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.description = kernel_function_metadata.description

    return mock_function


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_pre_invocation(pipeline_count):
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    result = FunctionResult(function=mock_function.metadata, value="test", metadata={})
    mock_function.invoke.return_value = result
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))

    invoked = 0

    def invoking_handler(kernel: Kernel, e: FunctionInvokingEventArgs) -> FunctionInvokingEventArgs:
        nonlocal invoked
        invoked += 1
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    functions = [mock_function] * pipeline_count

    # Act
    await kernel.invoke(functions, KernelArguments())

    # Assert
    assert invoked == pipeline_count
    assert mock_function.invoke.call_count == pipeline_count


@pytest.mark.asyncio
async def test_invoke_pre_invocation_skip_dont_trigger_invoked_handler():
    # Arrange
    kernel = Kernel()

    mock_function1 = create_mock_function(name="SkipMe")
    result1 = FunctionResult(function=mock_function1.metadata, value="test", metadata={})
    mock_function1.invoke.return_value = result1
    mock_function2 = create_mock_function(name="DontSkipMe")
    result2 = FunctionResult(function=mock_function2.metadata, value="test", metadata={})
    mock_function2.invoke.return_value = result2
    invoked = 0
    invoking = 0
    invoked_function_name = ""

    def invoking_handler(sender, e):
        nonlocal invoking
        invoking += 1
        if e.kernel_function_metadata.name == "SkipMe":
            e.skip()

    def invoked_handler(sender, e):
        nonlocal invoked_function_name, invoked
        invoked_function_name = e.kernel_function_metadata.name
        invoked += 1
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    _ = await kernel.invoke([mock_function1, mock_function2], KernelArguments())

    # Assert
    assert invoking == 2
    assert invoked == 1
    assert invoked_function_name == "DontSkipMe"


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_post_invocation(pipeline_count):
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    result = FunctionResult(function=mock_function.metadata, value="test", metadata={})
    mock_function.invoke.return_value = result
    invoked = 0

    def invoked_handler(sender, e):
        nonlocal invoked
        invoked += 1
        return e

    kernel.add_function_invoked_handler(invoked_handler)
    functions = [mock_function] * pipeline_count

    # Act
    _ = await kernel.invoke(functions, KernelArguments())

    # Assert
    assert invoked == pipeline_count
    mock_function.invoke.assert_called()
    assert mock_function.invoke.call_count == pipeline_count


@pytest.mark.asyncio
async def test_invoke_post_invocation_repeat_is_working():
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function(name="RepeatMe")
    result = FunctionResult(function=mock_function.metadata, value="test", metadata={})
    mock_function.invoke.return_value = result

    invoked = 0
    repeat_times = 0

    def invoked_handler(sender, e):
        nonlocal invoked, repeat_times
        invoked += 1

        if repeat_times < 3:
            e.repeat()
            repeat_times += 1
        return e

    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    _ = await kernel.invoke(mock_function)

    # Assert
    assert invoked == 4
    assert repeat_times == 3


@pytest.mark.asyncio
async def test_invoke_change_variable_invoking_handler():
    # Arrange
    kernel = Kernel()

    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function("test_function")
    result = FunctionResult(function=mock_function.metadata, value=new_input, metadata={})
    mock_function.invoke.return_value = result

    def invoking_handler(sender, e: FunctionInvokingEventArgs):
        e.arguments["input"] = new_input
        e.updated_arguments = True
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    arguments = KernelArguments(input=original_input)
    # Act
    result = await kernel.invoke([mock_function], arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


@pytest.mark.asyncio
async def test_invoke_change_variable_invoked_handler():
    # Arrange
    kernel = Kernel()

    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function("test_function")
    result = FunctionResult(function=mock_function.metadata, value=new_input, metadata={})
    mock_function.invoke.return_value = result

    def invoked_handler(sender, e: FunctionInvokedEventArgs):
        e.arguments["input"] = new_input
        e.updated_arguments = True
        return e

    kernel.add_function_invoked_handler(invoked_handler)
    arguments = KernelArguments(input=original_input)

    # Act
    result = await kernel.invoke(mock_function, arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
