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
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from semantic_kernel import Kernel
from semantic_kernel.exceptions.function_exceptions import FunctionInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction


@pytest.mark.asyncio
async def test_register_valid_native_function(
    kernel: Kernel, decorated_native_function: Callable
):
    kernel.add_function(plugin_name="TestPlugin", function=decorated_native_function)
    registered_func = kernel.get_function(
        plugin_name="TestPlugin", function_name="getLightStatus"
    )

    assert isinstance(registered_func, KernelFunction)
    assert (
        kernel.get_function(plugin_name="TestPlugin", function_name="getLightStatus")
        == registered_func
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
>>>>>>> Stashed changes
=======
import pytest

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_exception import KernelException


def not_decorated_native_function(arg1: str) -> str:
    return "test"


@kernel_function(name="getLightStatus")
def decorated_native_function(arg1: str) -> str:
    return "test"


@pytest.mark.asyncio
async def test_register_valid_native_function():
    kernel = Kernel()

    registered_func = kernel.register_native_function("TestPlugin", decorated_native_function)

    assert isinstance(registered_func, KernelFunction)
    assert kernel.plugins["TestPlugin"]["getLightStatus"] == registered_func
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
    func_result = await registered_func.invoke(kernel, KernelArguments(arg1="testtest"))
    assert str(func_result) == "test"


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
def test_register_undecorated_native_function(
    kernel: Kernel, not_decorated_native_function: Callable
):
    with pytest.raises(FunctionInitializationError):
        kernel.add_function("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name(
    kernel: Kernel, decorated_native_function: Callable
):
    with pytest.raises(ValidationError):
        kernel.add_function(function=decorated_native_function, plugin_name=None)
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
def test_register_undecorated_native_function():
    kernel = Kernel()

    with pytest.raises(KernelException):
        kernel.register_native_function("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name():
    kernel = Kernel()

    registered_func = kernel.register_native_function(None, decorated_native_function)
    assert registered_func.plugin_name is not None
    assert registered_func.plugin_name.startswith("p_")


def test_register_overloaded_native_function():
    kernel = Kernel()

    kernel.register_native_function("TestPlugin", decorated_native_function)

    with pytest.raises(ValueError):
        kernel.register_native_function("TestPlugin", decorated_native_function)
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
