# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView


def test_add_semantic_function():
    view = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_semantic=True,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(view)
    semantic_functions = functions_view.semantic_functions.get("plugin1")
    assert len(semantic_functions) == 1
    assert semantic_functions[0] == view


def test_add_native_function():
    view = FunctionView(
        name="function2",
        plugin_name="plugin2",
        description="Native function",
        parameters=[],
        is_semantic=False,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(view)
    native_functions = functions_view.native_functions.get("plugin2")
    assert len(native_functions) == 1
    assert native_functions[0] == view


def test_add_multiple_functions():
    semantic_function = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_semantic=True,
        is_asynchronous=True,
    )
    native_function = FunctionView(
        name="function2",
        plugin_name="plugin2",
        description="Native function",
        parameters=[],
        is_semantic=False,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(semantic_function)
    functions_view.add_function(native_function)
    semantic_functions = functions_view.semantic_functions.get("plugin1")
    native_functions = functions_view.native_functions.get("plugin2")
    assert len(semantic_functions) == 1
    assert semantic_functions[0] == semantic_function
    assert len(native_functions) == 1
    assert native_functions[0] == native_function


def test_is_semantic():
    semantic_function = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_semantic=True,
        is_asynchronous=True,
    )
    native_function = FunctionView(
        name="function2",
        plugin_name="plugin2",
        description="Native function",
        parameters=[],
        is_semantic=False,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(semantic_function)
    functions_view.add_function(native_function)
    assert functions_view.is_semantic("plugin1", "function1") is True
    assert functions_view.is_semantic("plugin2", "function2") is False
    assert functions_view.is_semantic("plugin1", "unregistered_function") is False


def test_is_native():
    semantic_function = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_semantic=True,
        is_asynchronous=True,
    )
    native_function = FunctionView(
        name="function2",
        plugin_name="plugin2",
        description="Native function",
        parameters=[],
        is_semantic=False,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(semantic_function)
    functions_view.add_function(native_function)
    assert functions_view.is_native("plugin1", "function1") is False
    assert functions_view.is_native("plugin2", "function2") is True
    assert functions_view.is_native("plugin2", "unregistered_function") is False


def test_ambiguous_implementation():
    semantic_function = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_semantic=True,
        is_asynchronous=True,
    )
    native_function = FunctionView(
        name="function1",
        plugin_name="plugin1",
        description="Native function",
        parameters=[],
        is_semantic=False,
        is_asynchronous=True,
    )
    functions_view = FunctionsView()
    functions_view.add_function(semantic_function)
    functions_view.add_function(native_function)

    with pytest.raises(KernelException) as exc_info:
        functions_view.is_semantic("plugin1", "function1")

    assert exc_info.value.error_code == KernelException.ErrorCodes.AmbiguousImplementation

    with pytest.raises(KernelException) as exc_info:
        functions_view.is_native("plugin1", "function1")

    assert exc_info.value.error_code == KernelException.ErrorCodes.AmbiguousImplementation
