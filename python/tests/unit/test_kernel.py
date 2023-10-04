from unittest.mock import AsyncMock, Mock

import pytest
from semantic_kernel import Kernel
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.function_view import FunctionView


def create_mock_function(name) -> SKFunctionBase:
    function_view = FunctionView(
        name, "SummarizeSkill", "Summarize an input", [], True, True
    )
    mock_function = Mock(spec=SKFunctionBase)
    mock_function.describe.return_value = function_view
    mock_function.name = function_view.name
    mock_function.skill_name = function_view.skill_name
    mock_function.description = function_view.description

    return mock_function


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_run_async_handles_pre_invocation(pipeline_count):
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    mock_function.invoke_async = AsyncMock(side_effect=lambda input, context: context)
    kernel._skill_collection.add_semantic_function(mock_function)

    invoked = 0

    def invoking_handler(sender, e):
        nonlocal invoked
        invoked += 1

    kernel.add_function_invoking_handler(invoking_handler)
    functions = [mock_function] * pipeline_count

    # Act
    _ = await kernel.run_async(*functions)

    # Assert
    assert invoked == pipeline_count
    assert mock_function.invoke_async.call_count == pipeline_count


@pytest.mark.asyncio
async def test_run_async_pre_invocation_skip_dont_trigger_invoked_handler():
    # Arrange
    kernel = Kernel()

    mock_function1 = create_mock_function(name="SkipMe")
    mock_function1.invoke_async = AsyncMock(side_effect=lambda input, context: context)
    mock_function2 = create_mock_function(name="DontSkipMe")
    mock_function2.invoke_async = AsyncMock(side_effect=lambda input, context: context)
    invoked = 0
    invoking = 0
    invoked_function_name = ""

    def invoking_handler(sender, e):
        nonlocal invoking
        invoking += 1
        if e.function_view.name == "SkipMe":
            e.skip()

    def invoked_handler(sender, e):
        nonlocal invoked_function_name, invoked
        invoked_function_name = e.function_view.name
        invoked += 1

    kernel.add_function_invoking_handler(invoking_handler)
    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    _ = await kernel.run_async(mock_function1, mock_function2)

    # Assert
    assert invoking == 2
    assert invoked == 1
    assert invoked_function_name == "DontSkipMe"


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_run_async_handles_post_invocation(pipeline_count):
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    mock_function.invoke_async = AsyncMock(side_effect=lambda input, context: context)
    invoked = 0

    def invoked_handler(sender, e):
        nonlocal invoked
        invoked += 1

    kernel.add_function_invoked_handler(invoked_handler)
    functions = [mock_function] * pipeline_count

    # Act
    _ = await kernel.run_async(*functions)

    # Assert
    assert invoked == pipeline_count
    mock_function.invoke_async.assert_called()
    assert mock_function.invoke_async.call_count == pipeline_count


@pytest.mark.asyncio
async def test_run_async_change_variable_invoking_handler():
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    mock_function.invoke_async = AsyncMock(side_effect=lambda input, context: context)

    original_input = "Importance"
    new_input = "Problems"

    def invoking_handler(sender, e):
        e.context.variables.update(new_input)
        e.context.variables["new"] = new_input

    kernel.add_function_invoking_handler(invoking_handler)

    # Act
    context = await kernel.run_async(mock_function, input_str=original_input)

    # Assert
    assert context.result == new_input
    assert context.variables.input == new_input
    assert context.variables["new"] == new_input


@pytest.mark.asyncio
async def test_run_async_change_variable_invoked_handler():
    # Arrange
    kernel = Kernel()

    mock_function = create_mock_function("test_function")
    mock_function.invoke_async = AsyncMock(side_effect=lambda input, context: context)

    original_input = "Importance"
    new_input = "Problems"

    def invoked_handler(sender, e):
        e.context.variables.update(new_input)
        e.context.variables["new"] = new_input

    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    context = await kernel.run_async(mock_function, input_str=original_input)

    # Assert
    assert context.result == new_input
    assert context.variables.input == new_input
    assert context.variables["new"] == new_input


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
