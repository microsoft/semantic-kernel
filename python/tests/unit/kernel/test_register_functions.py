# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Callable

import pytest
from pydantic import ValidationError

from semantic_kernel import Kernel
from semantic_kernel.exceptions.function_exceptions import FunctionInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction


async def test_register_valid_native_function(kernel: Kernel, decorated_native_function: Callable):
    kernel.add_function(plugin_name="TestPlugin", function=decorated_native_function)
    registered_func = kernel.get_function(plugin_name="TestPlugin", function_name="getLightStatus")

    assert isinstance(registered_func, KernelFunction)
    assert kernel.get_function(plugin_name="TestPlugin", function_name="getLightStatus") == registered_func
    func_result = await registered_func.invoke(kernel, KernelArguments(arg1="testtest"))
    assert str(func_result) == "test"


def test_register_undecorated_native_function(kernel: Kernel, not_decorated_native_function: Callable):
    with pytest.raises(FunctionInitializationError):
        kernel.add_function("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name(kernel: Kernel, decorated_native_function: Callable):
    with pytest.raises(ValidationError):
        kernel.add_function(function=decorated_native_function, plugin_name=None)
