# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.hooks.contexts import PostFunctionInvokeContext, PreFunctionInvokeContext
from semantic_kernel.hooks.kernel_hook_filter_decorator import kernel_hook_filter

# region Hooks


def test_hooks(kernel_with_hooks: Kernel):
    assert len(kernel_with_hooks._hooks) == 2


def test_add_hook_class_without_filters(kernel: Kernel):
    class TestHook:
        def __init__(self):
            self.invoked = False

        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.invoked = True

        def post_function_invoke(self, context: PostFunctionInvokeContext):
            self.invoked = True

    hook = TestHook()
    kernel.add_hook(hook)
    assert len(kernel._hooks) == 1


def test_add_hook_class_with_filters(kernel: Kernel):
    class TestHook:
        def __init__(self):
            self.invoked = False

        @kernel_hook_filter(include_functions=["test_function"])
        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.invoked = True

        @kernel_hook_filter(include_functions=["test_function"])
        def post_function_invoke(self, context: PostFunctionInvokeContext):
            self.invoked = True

    hook = TestHook()
    kernel.add_hook(hook)
    assert len(kernel._hooks) == 1


def test_add_hook_function(kernel: Kernel):
    def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel._hooks) == 1


def test_add_hook_function_with_filter(kernel: Kernel):
    @kernel_hook_filter(include_functions=["test_function"])
    def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel._hooks) == 1


def test_add_hook_async_function(kernel: Kernel):
    async def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel._hooks) == 1


def test_add_hook_async_function_with_filter(kernel: Kernel):
    @kernel_hook_filter(include_functions=["test_function"])
    async def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel._hooks) == 1


def test_add_hook_function_name(kernel: Kernel):
    def pre_function_invoke(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(pre_function_invoke)
    assert len(kernel._hooks) == 1


def test_add_hook_lambda(kernel: Kernel):
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel._hooks) == 1


def test_add_hook_with_position(kernel_with_hooks: Kernel):
    hook_id = kernel_with_hooks.add_hook(
        lambda context: print("\nRun after func..."), "post_function_invoke", position=0
    )
    assert len(kernel_with_hooks._hooks) == 3
    assert kernel_with_hooks._hooks[0][0] == hook_id


def test_remove_hook(kernel: Kernel):
    hook_id = kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel._hooks) == 1
    kernel.remove_hook(hook_id)
    assert len(kernel._hooks) == 0


def test_remove_hook_by_position(kernel: Kernel):
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel._hooks) == 1
    kernel.remove_hook(position=0)
    assert len(kernel._hooks) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_pre_invocation(kernel: Kernel, pipeline_count: int, create_mock_function):
    func = create_mock_function(name="test_function")
    kernel.plugins.add_plugin_from_functions("test", [func])
    invoked = 0

    def invoking_handler(context: PreFunctionInvokeContext) -> None:
        nonlocal invoked
        invoked += 1

    kernel.add_hook(invoking_handler, "pre_function_invoke")
    functions = [func] * pipeline_count

    # Act
    await kernel.invoke(functions, KernelArguments())

    # Assert
    assert func.call_count == pipeline_count
    assert invoked == pipeline_count


@pytest.mark.asyncio
async def test_invoke_pre_invocation_skip_dont_trigger_invoked_handler(kernel: Kernel, create_mock_function):
    mock_function1 = create_mock_function(name="SkipMe")
    mock_function2 = create_mock_function(name="DontSkipMe")
    invoked = 0
    invoking = 0
    invoked_function_name = ""

    def invoking_handler(context: PreFunctionInvokeContext):
        nonlocal invoking
        invoking += 1
        if context.kernel_function_metadata.name == "SkipMe":
            context.skip()

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked_function_name, invoked
        invoked_function_name = context.kernel_function_metadata.name
        invoked += 1

    kernel.add_hook(invoking_handler, "pre_function_invoke")
    kernel.add_hook(invoked_handler, "post_function_invoke")
    # Act
    _ = await kernel.invoke([mock_function1, mock_function2])

    # Assert
    assert invoking == 2
    assert invoked == 1
    assert invoked_function_name == "DontSkipMe"


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_post_invocation(kernel: Kernel, pipeline_count, create_mock_function):
    mock_function = create_mock_function("test_function")
    invoked = 0

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked
        invoked += 1

    kernel.add_hook(invoked_handler, "post_function_invoke")
    functions = [mock_function] * pipeline_count

    # Act
    _ = await kernel.invoke(functions)

    # Assert
    assert mock_function.call_count == pipeline_count
    assert invoked == pipeline_count


@pytest.mark.asyncio
async def test_invoke_post_invocation_repeat_is_working(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="RepeatMe")
    invoked = 0
    repeat_times = 0

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked, repeat_times
        invoked += 1

        if repeat_times < 3:
            context.repeat()
            repeat_times += 1

    kernel.add_hook(invoked_handler, "post_function_invoke")

    # Act
    _ = await kernel.invoke(mock_function)

    # Assert
    assert invoked == 4
    assert repeat_times == 3


@pytest.mark.asyncio
async def test_invoke_change_variable_invoking_handler(kernel: Kernel, create_mock_function):
    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function(name="test_function", value=new_input)

    def invoking_handler(context: PreFunctionInvokeContext):
        context.arguments["input"] = new_input
        context.updated_arguments = True

    kernel.add_hook(invoking_handler, "pre_function_invoke")
    arguments = KernelArguments(input=original_input)
    # Act
    result = await kernel.invoke([mock_function], arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


@pytest.mark.asyncio
async def test_invoke_change_variable_invoked_handler(kernel: Kernel, create_mock_function):
    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function(name="test_function", value=new_input)

    def invoked_handler(context: PostFunctionInvokeContext):
        context.arguments["input"] = new_input
        context.updated_arguments = True

    kernel.add_hook(invoked_handler, "post_function_invoke")
    arguments = KernelArguments(input=original_input)

    # Act
    result = await kernel.invoke(mock_function, arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


# endregion
