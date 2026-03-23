# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest

from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import (
    KernelProcessMessageChannel,
)
from semantic_kernel.processes.kernel_process.kernel_process_step_context import (
    KernelProcessStepContext,
)
from semantic_kernel.processes.step_utils import find_input_channels, get_fully_qualified_name


@pytest.fixture
def mock_function() -> Callable[..., Any]:
    @kernel_function
    def mock_function(input: str, context: KernelProcessStepContext) -> None:
        pass

    return mock_function


def test_find_input_channels_empty_functions():
    channel = MagicMock(spec=KernelProcessMessageChannel)
    functions = {}
    with pytest.raises(ValueError) as exc_info:
        find_input_channels(channel, functions)
    assert str(exc_info.value) == "The step has not been initialized."


def test_find_input_channels_with_required_params(mock_function):
    channel = MagicMock(spec=KernelProcessMessageChannel)

    function = KernelFunction.from_method(method=mock_function, plugin_name="test")

    functions = {"TestFunction": function}

    inputs = find_input_channels(channel, functions)

    assert "TestFunction" in inputs
    assert "input" in inputs["TestFunction"]
    assert "context" in inputs["TestFunction"]


@kernel_function
def skipped_function(param1: "Kernel", param2: int = 0) -> None:
    pass


def test_find_input_channels_with_only_skipped_params():
    channel = MagicMock(spec=KernelProcessMessageChannel)

    function = KernelFunction.from_method(method=skipped_function, plugin_name="test")
    functions = {"SkippedFunction": function}

    inputs = find_input_channels(channel, functions)

    expected_inputs = {"SkippedFunction": {}}

    assert inputs == expected_inputs


@kernel_function
def function1(param1: str) -> None:
    pass


@kernel_function
def function2(param2: KernelProcessStepContext, param3: float = 0.0) -> None:
    pass


def test_find_input_channels_multiple_functions():
    channel = MagicMock(spec=KernelProcessMessageChannel)

    function1_instance = KernelFunction.from_method(method=function1, plugin_name="test")
    function2_instance = KernelFunction.from_method(method=function2, plugin_name="test")

    functions = {
        "Function1": function1_instance,
        "Function2": function2_instance,
    }

    inputs = find_input_channels(channel, functions)

    assert "Function1" in inputs
    assert "param1" in inputs["Function1"]
    assert inputs["Function1"]["param1"] is None

    assert "Function2" in inputs
    assert "param2" in inputs["Function2"]
    assert isinstance(inputs["Function2"]["param2"], KernelProcessStepContext)
    assert "param3" not in inputs["Function2"]


def test_get_fully_qualified_name_standard_class():
    class TestClass:
        pass

    result = get_fully_qualified_name(TestClass)
    expected = f"{TestClass.__module__}.TestClass"
    assert result == expected


def test_get_fully_qualified_name_builtin_type():
    result = get_fully_qualified_name(int)
    expected = "builtins.int"
    assert result == expected


def test_get_fully_qualified_name_third_party_class():
    from unittest.mock import MagicMock

    result = get_fully_qualified_name(MagicMock)
    expected = "unittest.mock.MagicMock"
    assert result == expected


def test_get_fully_qualified_name_nested_class():
    class OuterClass:
        class InnerClass:
            pass

    result = get_fully_qualified_name(OuterClass.InnerClass)
    expected = f"{OuterClass.__module__}.InnerClass"
    assert result == expected


# --- Tests for get_step_class_from_qualified_name ---

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.step_utils import get_step_class_from_qualified_name


def test_get_step_class_empty_allowlist_blocks_all():
    """An empty allowlist sequence should block all modules."""
    with pytest.raises(ProcessInvalidConfigurationException, match="not in the allowed module prefixes"):
        get_step_class_from_qualified_name(
            "semantic_kernel.processes.kernel_process.kernel_process_step.KernelProcessStep",
            allowed_module_prefixes=[],
        )


def test_get_step_class_none_allowlist_allows_any():
    """Passing None should disable the allowlist check entirely."""
    from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep

    cls = get_step_class_from_qualified_name(
        "semantic_kernel.processes.kernel_process.kernel_process_step.KernelProcessStep",
        allowed_module_prefixes=None,
    )
    assert cls is KernelProcessStep


def test_get_step_class_prefix_without_dot_exact_match():
    """A prefix without a trailing dot should match the exact module name."""
    from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep

    cls = get_step_class_from_qualified_name(
        "semantic_kernel.processes.kernel_process.kernel_process_step.KernelProcessStep",
        allowed_module_prefixes=["semantic_kernel.processes.kernel_process.kernel_process_step"],
    )
    assert cls is KernelProcessStep


def test_get_step_class_prefix_without_dot_segment_boundary():
    """A prefix without a trailing dot must not match partial segment names."""
    with pytest.raises(ProcessInvalidConfigurationException, match="not in the allowed module prefixes"):
        get_step_class_from_qualified_name(
            "semantic_kernel_evil.some_module.SomeClass",
            allowed_module_prefixes=["semantic_kernel"],
        )


def test_get_step_class_prefix_with_dot_matches_submodule():
    """A prefix with a trailing dot should match submodules."""
    from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep

    cls = get_step_class_from_qualified_name(
        "semantic_kernel.processes.kernel_process.kernel_process_step.KernelProcessStep",
        allowed_module_prefixes=["semantic_kernel."],
    )
    assert cls is KernelProcessStep


def test_get_step_class_default_allowlist_blocks_non_sk_module():
    """Default allowlist should block modules outside semantic_kernel."""
    with pytest.raises(ProcessInvalidConfigurationException, match="not in the allowed module prefixes"):
        get_step_class_from_qualified_name("os.path.SomeClass")


def test_get_step_class_invalid_format():
    """Invalid class name format should raise an exception."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Invalid step class name format"):
        get_step_class_from_qualified_name("NoModule")
