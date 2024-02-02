# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel import Kernel
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.plugin_definition.kernel_function_decorator import kernel_function
from semantic_kernel.plugin_definition.plugin_collection import PluginCollection


def not_decorated_native_function(arg1: str) -> str:
    return "test"


@kernel_function(name="getLightStatus")
def decorated_native_function(arg1: str) -> str:
    return "test"


@pytest.mark.asyncio
async def test_register_valid_native_function():
    kernel = Kernel()

    registered_func = kernel.register_native_function("TestPlugin", decorated_native_function)

    assert isinstance(registered_func, KernelFunctionBase)
    assert kernel.plugins.get_native_function("TestPlugin", "getLightStatus") == registered_func
    func_result = await registered_func.invoke("testtest")
    assert func_result.result == "test"


def test_register_undecorated_native_function():
    kernel = Kernel()

    with pytest.raises(KernelException):
        kernel.register_native_function("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name():
    kernel = Kernel()

    registered_func = kernel.register_native_function(None, decorated_native_function)
    assert registered_func.plugin_name == PluginCollection.GLOBAL_PLUGIN


def test_register_overloaded_native_function():
    kernel = Kernel()

    kernel.register_native_function("TestPlugin", decorated_native_function)

    with pytest.raises(KernelException):
        kernel.register_native_function("TestPlugin", decorated_native_function)


if __name__ == "__main__":
    pytest.main([__file__])
