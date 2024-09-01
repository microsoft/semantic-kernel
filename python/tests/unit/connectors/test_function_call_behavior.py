# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


@pytest.fixture
def function_call_behavior():
    return FunctionCallBehavior()


@pytest.fixture
def update_settings_callback():
    mock = Mock()
    mock.return_value = None
    return mock


def test_function_call_behavior():
    fcb = FunctionCallBehavior()
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.max_auto_invoke_attempts == 5
    assert fcb.auto_invoke_kernel_functions is True


def test_function_call_behavior_get_set(function_call_behavior: FunctionCallBehavior):
    function_call_behavior.enable_kernel_functions = False
    assert function_call_behavior.enable_kernel_functions is False
    function_call_behavior.max_auto_invoke_attempts = 10
    assert function_call_behavior.max_auto_invoke_attempts == 10
    assert function_call_behavior.auto_invoke_kernel_functions is True
    function_call_behavior.auto_invoke_kernel_functions = False
    assert function_call_behavior.auto_invoke_kernel_functions is False
    assert function_call_behavior.max_auto_invoke_attempts == 0
    function_call_behavior.auto_invoke_kernel_functions = True
    assert function_call_behavior.auto_invoke_kernel_functions is True
    assert function_call_behavior.max_auto_invoke_attempts == 5


def test_auto_invoke_kernel_functions():
    fcb = FunctionCallBehavior.AutoInvokeKernelFunctions()
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.max_auto_invoke_attempts == 5
    assert fcb.auto_invoke_kernel_functions is True


def test_enable_kernel_functions():
    fcb = FunctionCallBehavior.EnableKernelFunctions()
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.max_auto_invoke_attempts == 0
    assert fcb.auto_invoke_kernel_functions is False


def test_enable_functions():
    fcb = FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"excluded_plugins": ["test"]}
    )
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.max_auto_invoke_attempts == 5
    assert fcb.auto_invoke_kernel_functions is True
    assert fcb.filters == {"excluded_plugins": ["test"]}


def test_required_function():
    fcb = FunctionCallBehavior.RequiredFunction(
        auto_invoke=True, function_fully_qualified_name="test"
    )
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.max_auto_invoke_attempts == 1
    assert fcb.auto_invoke_kernel_functions is True
    assert fcb.function_fully_qualified_name == "test"


def test_configure_default(
    function_call_behavior: FunctionCallBehavior,
    update_settings_callback,
    kernel: "Kernel",
):
    function_call_behavior.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_kernel_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.AutoInvokeKernelFunctions()
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_kernel_functions_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.AutoInvokeKernelFunctions()
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_enable_kernel_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.EnableKernelFunctions()
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_enable_kernel_functions_skip(
    update_settings_callback, kernel: "Kernel"
):
    fcb = FunctionCallBehavior.EnableKernelFunctions()
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_enable_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"excluded_plugins": ["test"]}
    )
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_enable_functions_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"excluded_plugins": ["test"]}
    )
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_required_function(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.RequiredFunction(
        auto_invoke=True, function_fully_qualified_name="test"
    )
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_required_function_max_invoke_updated(
    update_settings_callback, kernel: "Kernel"
):
    fcb = FunctionCallBehavior.RequiredFunction(
        auto_invoke=True, function_fully_qualified_name="test"
    )
    fcb.max_auto_invoke_attempts = 10
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called
    assert fcb.max_auto_invoke_attempts == 1


def test_configure_required_function_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionCallBehavior.RequiredFunction(
        auto_invoke=True, function_fully_qualified_name="test"
    )
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called
