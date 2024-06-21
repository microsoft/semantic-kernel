# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import pytest

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.function_choice_behavior import (
    DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS,
    FunctionChoiceBehavior,
    FunctionChoiceType,
    _check_for_missing_functions,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

kernel_function_metadata_set = {
    KernelFunctionMetadata(name="func1", plugin_name="plugin1", description="desc1", parameters=[], is_prompt=False),
    KernelFunctionMetadata(name="func2", plugin_name="plugin2", description="desc2", parameters=[], is_prompt=False),
}

kernel_function_metadata_list = list(kernel_function_metadata_set)


@pytest.fixture
def function_choice_behavior():
    return FunctionChoiceBehavior()


@pytest.fixture
def update_settings_callback():
    mock = Mock()
    mock.return_value = None
    return mock


def test_check_for_missing_functions_no_missing():
    function_names = ["plugin1-func1", "plugin2-func2"]
    _check_for_missing_functions(function_names, kernel_function_metadata_set)


def test_check_for_missing_functions_missing():
    function_names = ["func1", "func3"]
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        _check_for_missing_functions(function_names, kernel_function_metadata_set)


def test_function_choice_behavior_auto():
    behavior = FunctionChoiceBehavior.Auto(auto_invoke=True)
    assert behavior.type == FunctionChoiceType.AUTO
    assert behavior.maximum_auto_invoke_attempts == DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS


def test_function_choice_behavior_none_invoke():
    behavior = FunctionChoiceBehavior.NoneInvoke()
    assert behavior.type == FunctionChoiceType.NONE
    assert behavior.maximum_auto_invoke_attempts == 0


def test_function_choice_behavior_required():
    behavior = FunctionChoiceBehavior.Required(auto_invoke=True, function_fully_qualified_names=["plugin1-func1"])
    assert behavior.type == FunctionChoiceType.REQUIRED
    assert behavior.maximum_auto_invoke_attempts == 1
    assert behavior.function_fully_qualified_names == ["plugin1-func1"]


def test_from_function_call_behavior_kernel_functions():
    behavior = FunctionCallBehavior.AutoInvokeKernelFunctions()
    new_behavior = FunctionChoiceBehavior.from_function_call_behavior(behavior)
    assert new_behavior.type == FunctionChoiceType.AUTO
    assert new_behavior.auto_invoke_kernel_functions is True


def test_from_function_call_behavior_enabled_functions():
    expected_filters = {"included_functions": ["plugin1-func1"]}
    behavior = FunctionCallBehavior.EnableFunctions(auto_invoke=True, filters=expected_filters)
    new_behavior = FunctionChoiceBehavior.from_function_call_behavior(behavior)
    assert new_behavior.type == FunctionChoiceType.AUTO
    assert new_behavior.auto_invoke_kernel_functions is True
    assert new_behavior.filters == expected_filters


@pytest.mark.parametrize(("type", "max_auto_invoke_attempts"), [("auto", 5), ("none", 0), ("required", 1)])
def test_auto_function_choice_behavior_from_dict(type: str, max_auto_invoke_attempts: int):
    data = {
        "type": type,
        "functions": ["plugin1-func1", "plugin2-func2"],
        "filters": {"included_functions": ["plugin1-func1", "plugin2-func2"]},
        "maximum_auto_invoke_attempts": max_auto_invoke_attempts,
    }
    behavior = FunctionChoiceBehavior.from_dict(data)
    assert behavior.type == FunctionChoiceType(type)
    assert behavior.function_fully_qualified_names == ["plugin1-func1", "plugin2-func2"]
    assert behavior.filters == {"included_functions": ["plugin1-func1", "plugin2-func2"]}
    assert behavior.maximum_auto_invoke_attempts == max_auto_invoke_attempts


def test_function_choice_behavior_get_set(function_choice_behavior: FunctionChoiceBehavior):
    function_choice_behavior.enable_kernel_functions = False
    assert function_choice_behavior.enable_kernel_functions is False
    function_choice_behavior.maximum_auto_invoke_attempts = 10
    assert function_choice_behavior.maximum_auto_invoke_attempts == 10
    assert function_choice_behavior.auto_invoke_kernel_functions is True
    function_choice_behavior.auto_invoke_kernel_functions = False
    assert function_choice_behavior.auto_invoke_kernel_functions is False
    assert function_choice_behavior.maximum_auto_invoke_attempts == 0
    function_choice_behavior.auto_invoke_kernel_functions = True
    assert function_choice_behavior.auto_invoke_kernel_functions is True
    assert function_choice_behavior.maximum_auto_invoke_attempts == 5


def test_auto_invoke_kernel_functions():
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True)
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.maximum_auto_invoke_attempts == 5
    assert fcb.auto_invoke_kernel_functions is True


def test_none_invoke_kernel_functions():
    fcb = FunctionChoiceBehavior.NoneInvoke()
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.maximum_auto_invoke_attempts == 0
    assert fcb.auto_invoke_kernel_functions is False


def test_enable_functions():
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True, filters={"excluded_plugins": ["test"]})
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.maximum_auto_invoke_attempts == 5
    assert fcb.auto_invoke_kernel_functions is True
    assert fcb.filters == {"excluded_plugins": ["test"]}


def test_required_function():
    fcb = FunctionChoiceBehavior.Required(auto_invoke=True, function_fully_qualified_names=["test"])
    assert fcb is not None
    assert fcb.enable_kernel_functions is True
    assert fcb.maximum_auto_invoke_attempts == 1
    assert fcb.auto_invoke_kernel_functions is True
    assert fcb.function_fully_qualified_names == ["test"]


def test_configure_auto_invoke_kernel_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True)
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_auto_invoke_kernel_functions_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True)
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_none_invoke_kernel_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.NoneInvoke()
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_none_invoke_kernel_functions_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.NoneInvoke()
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_enable_functions(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True, filters={"excluded_plugins": ["test"]})
    fcb.configure(kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_enable_functions_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.Auto(auto_invoke=True, filters={"excluded_plugins": ["test"]})
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called


def test_configure_required_function(update_settings_callback, kernel: "Kernel"):
    mock_kernel = MagicMock()
    mock_kernel.get_full_list_of_function_metadata.return_value = kernel_function_metadata_list
    mock_kernel.get_list_of_function_metadata.return_value = kernel_function_metadata_list

    fcb = FunctionChoiceBehavior.Required(auto_invoke=True, function_fully_qualified_names=["plugin1-func1"])
    fcb.configure(mock_kernel, update_settings_callback, None)
    assert update_settings_callback.called


def test_configure_required_function_max_invoke_updated(update_settings_callback, kernel: "Kernel"):
    mock_kernel = MagicMock()
    mock_kernel.get_full_list_of_function_metadata.return_value = kernel_function_metadata_list
    mock_kernel.get_list_of_function_metadata.return_value = kernel_function_metadata_list

    fcb = FunctionChoiceBehavior.Required(auto_invoke=True, function_fully_qualified_names=["plugin1-func1"])
    fcb.maximum_auto_invoke_attempts = 10
    fcb.configure(mock_kernel, update_settings_callback, None)
    assert update_settings_callback.called
    assert fcb.maximum_auto_invoke_attempts == 1


def test_configure_required_function_skip(update_settings_callback, kernel: "Kernel"):
    fcb = FunctionChoiceBehavior.Required(auto_invoke=True, function_fully_qualified_names=["test"])
    fcb.enable_kernel_functions = False
    fcb.configure(kernel, update_settings_callback, None)
    assert not update_settings_callback.called
