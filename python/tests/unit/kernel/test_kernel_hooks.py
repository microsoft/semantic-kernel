# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel import Kernel
from semantic_kernel.exceptions.kernel_exceptions import HookInvalidSignatureError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.hooks import PostFunctionInvokeContext, PreFunctionInvokeContext
from semantic_kernel.hooks.kernel_hook_filter_decorator import kernel_hook_filter
from semantic_kernel.hooks.prompt.post_prompt_render_context import PostPromptRenderContext
from semantic_kernel.hooks.prompt.pre_prompt_render_context import PrePromptRenderContext

# region Hooks


def test_hooks(kernel_with_hooks: Kernel):
    assert len(kernel_with_hooks.hooks) == 2


def test_add_hook_class_without_filters(kernel: Kernel):
    class TestHook:
        def __init__(self):
            self.invoked = False

        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.invoked = True

        def post_function_invoke(self, context: PostFunctionInvokeContext):
            self.invoked = True

        def pre_prompt_render(self, context: PrePromptRenderContext):
            self.invoked = True

        def post_prompt_render(self, context: PostPromptRenderContext):
            self.invoked = True

    hook = TestHook()
    kernel.add_hook(hook)
    assert len(kernel.hooks) == 1


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

        @kernel_hook_filter(include_functions=["test_function"])
        def pre_prompt_render(self, context: PrePromptRenderContext):
            self.invoked = True

        @kernel_hook_filter(include_functions=["test_function"])
        def post_prompt_render(self, context: PostPromptRenderContext):
            self.invoked = True

    hook = TestHook()
    kernel.add_hook(hook)
    assert len(kernel.hooks) == 1


def test_add_hook_function(kernel: Kernel):
    def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel.hooks) == 1


def test_add_hook_function_with_filter(kernel: Kernel):
    @kernel_hook_filter(include_functions=["test_function"])
    def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel.hooks) == 1


def test_add_hook_async_function(kernel: Kernel):
    async def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel.hooks) == 1


def test_add_hook_async_function_with_filter(kernel: Kernel):
    @kernel_hook_filter(include_functions=["test_function"])
    async def hook(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(hook, "pre_function_invoke")
    assert len(kernel.hooks) == 1


def test_add_hook_function_name(kernel: Kernel):
    def pre_function_invoke(context: PreFunctionInvokeContext):
        pass

    kernel.add_hook(pre_function_invoke)
    assert len(kernel.hooks) == 1


def test_add_hook_lambda(kernel: Kernel):
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel.hooks) == 1


def test_add_hook_with_position(kernel_with_hooks: Kernel):
    hook_id = kernel_with_hooks.add_hook(
        lambda context: print("\nRun after func..."), "post_function_invoke", position=0
    )
    assert len(kernel_with_hooks.hooks) == 3
    assert kernel_with_hooks.hooks[0][0] == hook_id


def test_remove_hook(kernel: Kernel):
    hook_id = kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel.hooks) == 1
    kernel.remove_hook(hook_id)
    assert len(kernel.hooks) == 0


def test_remove_hook_by_position(kernel: Kernel):
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel.hooks) == 1
    kernel.remove_hook(position=0)
    assert len(kernel.hooks) == 0


def test_remove_hook_fail(kernel: Kernel):
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")
    assert len(kernel.hooks) == 1
    with pytest.raises(ValueError):
        kernel.remove_hook()


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
async def test_invoke_all_hooks(kernel: Kernel, create_mock_function):
    func = create_mock_function(name="test_function")

    class TestHook:
        def __init__(self):
            self.pre_function_invoke_flag = False
            self.post_function_invoke_flag = False
            self.pre_prompt_render_flag = False
            self.post_prompt_render_flag = False

        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.pre_function_invoke_flag = True

        def post_function_invoke(self, context: PostFunctionInvokeContext):
            self.post_function_invoke_flag = True

        def pre_prompt_render(self, context: PrePromptRenderContext):
            self.pre_prompt_render_flag = True

        def post_prompt_render(self, context: PostPromptRenderContext):
            self.post_prompt_render_flag = True

    hook = TestHook()
    kernel.add_hook(hook)

    # Act
    await kernel.invoke(func, KernelArguments())

    # Assert
    assert hook.pre_function_invoke_flag
    assert hook.post_function_invoke_flag
    assert hook.pre_prompt_render_flag
    assert hook.post_prompt_render_flag


@pytest.mark.asyncio
async def test_invoke_all_hooks_async(kernel: Kernel, create_mock_function):
    func = create_mock_function(name="test_function")

    class TestHook:
        def __init__(self):
            self.pre_function_invoke_flag = False
            self.post_function_invoke_flag = False
            self.pre_prompt_render_flag = False
            self.post_prompt_render_flag = False

        async def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.pre_function_invoke_flag = True

        async def post_function_invoke(self, context: PostFunctionInvokeContext):
            self.post_function_invoke_flag = True

        async def pre_prompt_render(self, context: PrePromptRenderContext):
            self.pre_prompt_render_flag = True

        async def post_prompt_render(self, context: PostPromptRenderContext):
            self.post_prompt_render_flag = True

    hook = TestHook()
    kernel.add_hook(hook)

    # Act
    await kernel.invoke(func, KernelArguments())

    # Assert
    assert hook.pre_function_invoke_flag
    assert hook.post_function_invoke_flag
    assert hook.pre_prompt_render_flag
    assert hook.post_prompt_render_flag


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
        if context.function.name == "SkipMe":
            context.skip()

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked_function_name, invoked
        invoked_function_name = context.function.name
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
async def test_invoke_pre_invocation_cancel(kernel: Kernel, create_mock_function):
    mock_function1 = create_mock_function(name="test")
    invoked = 0

    def invoking_handler(context: PreFunctionInvokeContext):
        context.cancel()

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked
        invoked += 1

    kernel.add_hook(invoking_handler, "pre_function_invoke")
    kernel.add_hook(invoked_handler, "post_function_invoke")
    # Act
    _ = await kernel.invoke(mock_function1)

    # Assert
    assert invoked == 0


@pytest.mark.asyncio
async def test_invoke_post_invocation_cancel(kernel: Kernel, create_mock_function):
    mock_function1 = create_mock_function(name="test")
    invoked = 0

    def invoked_handler(context: PostFunctionInvokeContext):
        nonlocal invoked
        invoked += 1
        context.cancel()

    def invoked_handler2(context: PostFunctionInvokeContext):
        nonlocal invoked
        invoked += 1

    kernel.add_hook(invoked_handler, "post_function_invoke")
    kernel.add_hook(invoked_handler2, "post_function_invoke")
    # Act
    _ = await kernel.invoke(mock_function1)

    # Assert
    assert invoked == 1


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
    pre_prompt_invoked = 0

    mock_function = create_mock_function(name="test_function", value=new_input)

    def invoking_handler(context: PreFunctionInvokeContext):
        context.update_arguments(KernelArguments(input=new_input))

    def pre_prompt_render(context: PrePromptRenderContext):
        nonlocal pre_prompt_invoked
        pre_prompt_invoked += 1
        assert context.arguments["input"] == new_input

    kernel.add_hook(invoking_handler, "pre_function_invoke")
    kernel.add_hook(pre_prompt_render, "pre_prompt_render")
    # Act
    result = await kernel.invoke([mock_function], arguments=KernelArguments(input=original_input))

    # Assert
    assert pre_prompt_invoked == 1
    assert str(result) == new_input


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


def test_name_fail(kernel: Kernel):
    def hook(context: PreFunctionInvokeContext):
        pass

    with pytest.raises(HookInvalidSignatureError):
        kernel.add_hook(hook)


def test_name_fail_supplied(kernel: Kernel):
    def hook(context: PreFunctionInvokeContext):
        pass

    with pytest.raises(HookInvalidSignatureError):
        kernel.add_hook(hook, "other_name")


def test_protocol_fail(kernel: Kernel):
    def hook(context: PreFunctionInvokeContext, other: int):
        pass

    with pytest.raises(HookInvalidSignatureError):
        kernel.add_hook(hook, "post_function_invoke")


def test_method_signature_fail(kernel: Kernel):
    class TestHook:
        def pre_function_invoke(self, context: PreFunctionInvokeContext, other: int):
            pass

    with pytest.raises(HookInvalidSignatureError):
        kernel.add_hook(TestHook())


def test_empty_hook_class(kernel: Kernel):
    class TestHook:
        pass

    with pytest.raises(HookInvalidSignatureError):
        kernel.add_hook(TestHook())


@pytest.mark.asyncio
async def test_invoke_exception_non_blocking(kernel: Kernel, create_mock_function):
    original_input = "Importance"

    mock_function = create_mock_function(name="test_function", value="Importance")

    class TestHook:
        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            raise Exception("Test Exception")

        def post_function_invoke(self, context: PostFunctionInvokeContext):
            raise Exception("Test Exception")

        def pre_prompt_render(self, context: PrePromptRenderContext):
            raise Exception("Test Exception")

        def post_prompt_render(self, context: PostPromptRenderContext):
            raise Exception("Test Exception")

    kernel.add_hook(TestHook())
    arguments = KernelArguments(input=original_input)

    # Act
    result = await kernel.invoke(mock_function, arguments)

    # Assert
    assert str(result) == "Importance"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filter, flag",
    [
        ({"include_functions": ["func"]}, True),
        ({"include_functions": ["func2"]}, False),
        ({"exclude_functions": ["func"]}, False),
        ({"include_plugins": ["TestPlugin"]}, True),
        ({"include_plugins": ["plugin"]}, False),
        ({"exclude_plugins": ["TestPlugin"]}, False),
    ],
)
async def test_filtering(kernel: Kernel, filter: dict, flag: bool, create_mock_function):
    input = "Importance"

    mock_function = create_mock_function(name="func", value=input)

    class TestHook:
        def __init__(self):
            self.pre_function_invoke_flag = False

        @kernel_hook_filter(**filter)
        def pre_function_invoke(self, context: PreFunctionInvokeContext):
            self.pre_function_invoke_flag = True

    hook = TestHook()
    kernel.add_hook(hook)
    arguments = KernelArguments(input=input)

    # Act
    await kernel.invoke(mock_function, arguments)

    # Assert
    assert hook.pre_function_invoke_flag == flag
