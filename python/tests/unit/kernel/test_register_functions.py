# Copyright (c) Microsoft. All rights reserved.


import pytest
from pydantic import ValidationError

from semantic_kernel import Kernel
from semantic_kernel.exceptions import FunctionInitializationError
from semantic_kernel.exceptions.function_exceptions import FunctionInvalidNameError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function


def not_decorated_native_function(arg1: str) -> str:
    return "test"


@kernel_function(name="getLightStatus")
def decorated_native_function(arg1: str) -> str:
    return "test"


@pytest.mark.asyncio
async def test_register_valid_native_function():
    kernel = Kernel()

    registered_func = kernel.register_function_from_method("TestPlugin", decorated_native_function)

    assert isinstance(registered_func, KernelFunction)
    assert kernel.plugins["TestPlugin"]["getLightStatus"] == registered_func
    func_result = await registered_func.invoke(kernel, KernelArguments(arg1="testtest"))
    assert str(func_result) == "test"


def test_register_undecorated_native_function():
    kernel = Kernel()

    with pytest.raises(FunctionInitializationError):
        kernel.register_function_from_method("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name():
    kernel = Kernel()

    with pytest.raises(ValidationError):
        kernel.register_function_from_method(method=decorated_native_function, plugin_name=None)


def test_register_overloaded_native_function():
    kernel = Kernel()

    kernel.register_function_from_method("TestPlugin", decorated_native_function)

    with pytest.raises(FunctionInvalidNameError):
        kernel.register_function_from_method("TestPlugin", decorated_native_function)
