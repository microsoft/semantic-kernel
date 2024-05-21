# Copyright (c) Microsoft. All rights reserved.
from collections.abc import AsyncGenerator, Iterable
from typing import Annotated, Any

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel


def test_init_native_function_with_input_description():
    @kernel_function(description="Mock description", name="mock_function")
    def mock_function(input: Annotated[str, "input"], arguments: "KernelArguments") -> None:
        pass

    mock_method = mock_function

    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

    assert native_function.method == mock_method
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "input"
    assert not native_function.parameters[0].default_value
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].is_required is True
    assert native_function.parameters[1].name == "arguments"
    assert native_function.parameters[1].description is None
    assert not native_function.parameters[1].default_value
    assert native_function.parameters[1].type_ == "KernelArguments"
    assert native_function.parameters[1].is_required is True


def test_init_native_function_without_input_description():
    @kernel_function()
    def mock_function(arguments: "KernelArguments") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function_no_input_desc"
    mock_function.__kernel_function_description__ = "Mock description no input desc"
    mock_function.__kernel_function_parameters__ = [
        {
            "name": "arguments",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
            "is_required": True,
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

    assert native_function.method == mock_method
    assert native_function.parameters[0].name == "arguments"
    assert native_function.parameters[0].description == "Param 1 description"
    assert native_function.parameters[0].default_value == "default_param1_value"
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].is_required is True


def test_init_native_function_from_kernel_function_decorator():
    @kernel_function(
        description="Test description",
        name="test_function",
    )
    def decorated_function(input: Annotated[str | None, "Test input description"] = "test_default_value") -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ == "Test description"
    assert decorated_function.__kernel_function_name__ == "test_function"

    native_function = KernelFunction.from_method(method=decorated_function, plugin_name="MockPlugin")

    assert native_function.method == decorated_function
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "Test input description"
    assert native_function.parameters[0].default_value == "test_default_value"
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].is_required is False


def test_init_native_function_from_kernel_function_decorator_defaults():
    @kernel_function()
    def decorated_function() -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ is None
    assert decorated_function.__kernel_function_name__ == "decorated_function"

    native_function = KernelFunction.from_method(method=decorated_function, plugin_name="MockPlugin")

    assert native_function.method == decorated_function
    assert len(native_function.parameters) == 0


def test_init_method_is_none():
    with pytest.raises(FunctionInitializationError):
        KernelFunction.from_method(method=None, plugin_name="MockPlugin")


def test_init_method_is_not_kernel_function():
    def not_kernel_function():
        pass

    with pytest.raises(FunctionInitializationError):
        KernelFunction.from_method(method=not_kernel_function, plugin_name="MockPlugin")


def test_init_invalid_name():
    @kernel_function(name="invalid name")
    def invalid_name():
        pass

    with pytest.raises(FunctionInitializationError):
        KernelFunction.from_method(method=invalid_name, plugin_name="MockPlugin")


@pytest.mark.asyncio
async def test_invoke_non_async(kernel: Kernel):
    @kernel_function()
    def non_async_function() -> str:
        return ""

    native_function = KernelFunction.from_method(method=non_async_function, plugin_name="MockPlugin")

    result = await native_function.invoke(kernel=kernel, arguments=None)
    assert result.value == ""

    with pytest.raises(NotImplementedError):
        async for _ in native_function.invoke_stream(kernel=kernel, arguments=None):
            pass


@pytest.mark.asyncio
async def test_invoke_async(kernel: Kernel):
    @kernel_function()
    async def async_function() -> str:
        return ""

    native_function = KernelFunction.from_method(method=async_function, plugin_name="MockPlugin")

    result = await native_function.invoke(kernel=kernel, arguments=None)
    assert result.value == ""

    with pytest.raises(NotImplementedError):
        async for _ in native_function.invoke_stream(kernel=kernel, arguments=None):
            pass


@pytest.mark.asyncio
async def test_invoke_gen(kernel: Kernel):
    @kernel_function()
    def gen_function() -> Iterable[str]:
        yield ""

    native_function = KernelFunction.from_method(method=gen_function, plugin_name="MockPlugin")

    result = await native_function.invoke(kernel=kernel, arguments=None)
    assert result.value == [""]

    async for partial_result in native_function.invoke_stream(kernel=kernel, arguments=None):
        assert partial_result == ""


@pytest.mark.asyncio
async def test_invoke_gen_async(kernel: Kernel):
    @kernel_function()
    async def async_gen_function() -> AsyncGenerator[str, Any]:
        yield ""

    native_function = KernelFunction.from_method(method=async_gen_function, plugin_name="MockPlugin")

    result = await native_function.invoke(kernel=kernel, arguments=None)
    assert result.value == [""]

    async for partial_result in native_function.invoke_stream(kernel=kernel, arguments=None):
        assert partial_result == ""


@pytest.mark.asyncio
async def test_service_execution(kernel: Kernel, openai_unit_test_env):
    service = OpenAIChatCompletion(service_id="test", ai_model_id="test")
    req_settings = service.get_prompt_execution_settings_class()(service_id="test")
    req_settings.temperature = 0.5
    kernel.add_service(service)
    arguments = KernelArguments(settings=req_settings)

    @kernel_function(name="function")
    def my_function(kernel, service, execution_settings, arguments) -> str:
        assert kernel is not None
        assert isinstance(kernel, Kernel)
        assert service is not None
        assert isinstance(service, OpenAIChatCompletion)
        assert execution_settings is not None
        assert isinstance(execution_settings, req_settings.__class__)
        assert execution_settings.temperature == 0.5
        assert arguments is not None
        assert isinstance(arguments, KernelArguments)
        return "ok"

    func = KernelFunction.from_method(my_function, "test")

    result = await func.invoke(kernel, arguments)
    assert result.value == "ok"


@pytest.mark.asyncio
async def test_required_param_not_supplied(kernel: Kernel):
    @kernel_function()
    def my_function(input: str) -> str:
        return input

    func = KernelFunction.from_method(my_function, "test")

    with pytest.raises(FunctionExecutionException):
        await func.invoke(kernel=kernel, arguments=KernelArguments())


@pytest.mark.asyncio
async def test_service_execution_with_complex_object(kernel: Kernel):
    class InputObject(KernelBaseModel):
        arg1: str
        arg2: int

    @kernel_function(name="function")
    def my_function(input_obj: InputObject) -> str:
        assert input_obj is not None
        assert isinstance(input_obj, InputObject)
        assert input_obj.arg1 == "test"
        assert input_obj.arg2 == 5
        return f"{input_obj.arg1} {input_obj.arg2}"

    func = KernelFunction.from_method(my_function, "test")

    arguments = KernelArguments(input_obj=InputObject(arg1="test", arg2=5))
    result = await func.invoke(kernel, arguments)
    assert result.value == "test 5"


class InputObject(KernelBaseModel):
    arg1: str
    arg2: int


@pytest.mark.asyncio
async def test_service_execution_with_complex_object_from_str(kernel: Kernel):
    @kernel_function(name="function")
    def my_function(input_obj: InputObject) -> str:
        assert input_obj is not None
        assert isinstance(input_obj, InputObject)
        assert input_obj.arg1 == "test"
        assert input_obj.arg2 == 5
        return f"{input_obj.arg1} {input_obj.arg2}"

    func = KernelFunction.from_method(my_function, "test")

    arguments = KernelArguments(input_obj={"arg1": "test", "arg2": 5})
    result = await func.invoke(kernel, arguments)
    assert result.value == "test 5"


@pytest.mark.asyncio
async def test_service_execution_with_complex_object_from_str_mixed(kernel: Kernel):
    @kernel_function(name="function")
    def my_function(input_obj: InputObject, input_str: str) -> str:
        assert input_obj is not None
        assert isinstance(input_obj, InputObject)
        assert input_obj.arg1 == "test"
        assert input_obj.arg2 == 5
        return f"{input_obj.arg1} {input_str} {input_obj.arg2}"

    func = KernelFunction.from_method(my_function, "test")

    arguments = KernelArguments(input_obj={"arg1": "test", "arg2": 5}, input_str="test2")
    result = await func.invoke(kernel, arguments)
    assert result.value == "test test2 5"


@pytest.mark.asyncio
async def test_service_execution_with_complex_object_from_str_mixed_multi(kernel: Kernel):
    @kernel_function(name="function")
    def my_function(input_obj: InputObject, input_str: str | int) -> str:
        assert input_obj is not None
        assert isinstance(input_obj, InputObject)
        assert input_obj.arg1 == "test"
        assert input_obj.arg2 == 5
        return f"{input_obj.arg1} {input_str} {input_obj.arg2}"

    func = KernelFunction.from_method(my_function, "test")

    arguments = KernelArguments(input_obj={"arg1": "test", "arg2": 5}, input_str="test2")
    result = await func.invoke(kernel, arguments)
    assert result.value == "test test2 5"


def test_function_from_lambda():
    func = KernelFunctionFromMethod(method=kernel_function(lambda x: x**2, name="square"), plugin_name="math")
    assert func is not None


@pytest.mark.asyncio
async def test_function_invocation_filters(kernel: Kernel):
    func = KernelFunctionFromMethod(method=kernel_function(lambda input: input**2, name="square"), plugin_name="math")
    kernel.add_function(plugin_name="math", function=func)

    pre_call_count = 0
    post_call_count = 0

    async def custom_filter(context, next):
        nonlocal pre_call_count
        pre_call_count += 1
        await next(context)
        nonlocal post_call_count
        post_call_count += 1

    kernel.add_filter("function_invocation", custom_filter)
    result = await kernel.invoke(plugin_name="math", function_name="square", arguments=KernelArguments(input=2))
    assert result.value == 4
    assert pre_call_count == 1
    assert post_call_count == 1


@pytest.mark.asyncio
async def test_function_invocation_multiple_filters(kernel: Kernel):
    call_stack = []

    @kernel_function(name="square")
    def func(input: int):
        nonlocal call_stack
        call_stack.append("func")
        return input**2

    kernel.add_function(plugin_name="math", function=func)

    async def custom_filter1(context, next):
        nonlocal call_stack
        call_stack.append("custom_filter1_pre")
        await next(context)
        call_stack.append("custom_filter1_post")

    async def custom_filter2(context, next):
        nonlocal call_stack
        call_stack.append("custom_filter2_pre")
        await next(context)
        call_stack.append("custom_filter2_post")

    kernel.add_filter("function_invocation", custom_filter1)
    kernel.add_filter("function_invocation", custom_filter2)
    result = await kernel.invoke(plugin_name="math", function_name="square", arguments=KernelArguments(input=2))
    assert result.value == 4
    assert call_stack == [
        "custom_filter1_pre",
        "custom_filter2_pre",
        "func",
        "custom_filter2_post",
        "custom_filter1_post",
    ]


@pytest.mark.asyncio
async def test_function_invocation_filters_streaming(kernel: Kernel):
    call_stack = []

    @kernel_function(name="square")
    async def func(input: int):
        nonlocal call_stack
        call_stack.append("func1")
        yield input**2
        call_stack.append("func2")
        yield input**3

    kernel.add_function(plugin_name="math", function=func)

    async def custom_filter(context, next):
        nonlocal call_stack
        call_stack.append("custom_filter_pre")
        await next(context)

        async def override_stream(stream):
            nonlocal call_stack
            async for partial in stream:
                call_stack.append("overridden_func")
                yield partial * 2

        stream = context.result.value
        context.result = FunctionResult(function=context.result.function, value=override_stream(stream))
        call_stack.append("custom_filter_post")

    kernel.add_filter("function_invocation", custom_filter)
    index = 0
    async for partial in kernel.invoke_stream(
        plugin_name="math", function_name="square", arguments=KernelArguments(input=2)
    ):
        assert partial == 8 if index == 0 else 16
        index += 1
    assert call_stack == [
        "custom_filter_pre",
        "custom_filter_post",
        "func1",
        "overridden_func",
        "func2",
        "overridden_func",
    ]
