# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel import Kernel
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.plugin_definition.plugin_collection import PluginCollection
from semantic_kernel.plugin_definition.sk_function_decorator import sk_function


def not_decorated_native_function(arg1: str) -> str:
    return "test"


@sk_function(name="getLightStatus")
def decorated_native_function(arg1: str) -> str:
    return "test"


def test_register_valid_native_function():
    kernel = Kernel()

    registered_func = kernel.register_native_function("TestPlugin", decorated_native_function)

    assert isinstance(registered_func, SKFunctionBase)
    assert kernel.plugins.get_native_function("TestPlugin", "getLightStatus") == registered_func
    assert registered_func.invoke("testtest").result == "test"


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
