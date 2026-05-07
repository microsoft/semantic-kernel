# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_kernel_arguments():
    kargs = KernelArguments()
    assert kargs is not None
    assert kargs.execution_settings is None
    assert not kargs.keys()


def test_kernel_arguments_with_input():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert kargs["input"] == 10


def test_kernel_arguments_with_input_get():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert kargs.get("input", None) == 10
    assert not kargs.get("input2", None)


def test_kernel_arguments_keys():
    kargs = KernelArguments(input=10)
    assert kargs is not None
    assert list(kargs.keys()) == ["input"]


def test_kernel_arguments_with_execution_settings():
    test_pes = PromptExecutionSettings(service_id="test")
    kargs = KernelArguments(settings=[test_pes])
    assert kargs is not None
    assert kargs.execution_settings == {"test": test_pes}


def test_kernel_arguments_bool():
    # An empty KernelArguments object should return False
    assert not KernelArguments()
    # An KernelArguments object with keyword arguments should return True
    assert KernelArguments(input=10)
    # An KernelArguments object with execution_settings should return True
    assert KernelArguments(settings=PromptExecutionSettings(service_id="test"))
    # An KernelArguments object with both keyword arguments and execution_settings should return True
    assert KernelArguments(input=10, settings=PromptExecutionSettings(service_id="test"))


@pytest.mark.parametrize(
    "lhs, rhs, expected_dict, expected_settings_keys",
    [
        # Merging different keys
        (KernelArguments(a=1), KernelArguments(b=2), {"a": 1, "b": 2}, None),
        # RHS overwrites when keys duplicate
        (KernelArguments(a=1), KernelArguments(a=99), {"a": 99}, None),
        # Merging with a plain dict
        (KernelArguments(a=1), {"b": 2}, {"a": 1, "b": 2}, None),
        # Merging execution_settings together
        (
            KernelArguments(settings=PromptExecutionSettings(service_id="s1")),
            KernelArguments(settings=PromptExecutionSettings(service_id="s2")),
            {},
            ["s1", "s2"],
        ),
        # Same service_id is overwritten by RHS
        (
            KernelArguments(settings=PromptExecutionSettings(service_id="shared")),
            KernelArguments(settings=PromptExecutionSettings(service_id="shared")),
            {},
            ["shared"],
        ),
    ],
)
def test_kernel_arguments_or_operator(lhs, rhs, expected_dict, expected_settings_keys):
    """Test the __or__ operator (lhs | rhs) with various argument combinations."""
    result = lhs | rhs
    assert isinstance(result, KernelArguments)
    assert dict(result) == expected_dict
    if expected_settings_keys is None:
        assert result.execution_settings is None
    else:
        assert sorted(result.execution_settings.keys()) == sorted(expected_settings_keys)


@pytest.mark.parametrize("rhs", [42, "foo", None])
def test_kernel_arguments_or_operator_with_invalid_type(rhs):
    """Test the __or__ operator with an invalid type raises TypeError."""
    with pytest.raises(TypeError):
        KernelArguments() | rhs


@pytest.mark.parametrize(
    "lhs, rhs, expected_dict, expected_settings_keys",
    [
        # Dict merge (in-place)
        (KernelArguments(a=1), {"b": 2}, {"a": 1, "b": 2}, None),
        # Merging between KernelArguments
        (KernelArguments(a=1), KernelArguments(b=2), {"a": 1, "b": 2}, None),
        # Retain existing execution_settings after dict merge
        (KernelArguments(a=1, settings=PromptExecutionSettings(service_id="s1")), {"b": 2}, {"a": 1, "b": 2}, ["s1"]),
        # In-place merge of execution_settings
        (
            KernelArguments(settings=PromptExecutionSettings(service_id="s1")),
            KernelArguments(settings=PromptExecutionSettings(service_id="s2")),
            {},
            ["s1", "s2"],
        ),
    ],
)
def test_kernel_arguments_inplace_merge(lhs, rhs, expected_dict, expected_settings_keys):
    """Test the |= operator with various argument combinations without execution_settings."""
    original_id = id(lhs)
    lhs |= rhs
    # Verify this is the same object (in-place)
    assert id(lhs) == original_id
    assert dict(lhs) == expected_dict
    if expected_settings_keys is None:
        assert lhs.execution_settings is None
    else:
        assert sorted(lhs.execution_settings.keys()) == sorted(expected_settings_keys)


@pytest.mark.parametrize(
    "rhs, lhs, expected_dict, expected_settings_keys",
    [
        # Merging different keys
        ({"b": 2}, KernelArguments(a=1), {"b": 2, "a": 1}, None),
        # RHS overwrites when keys duplicate
        ({"a": 1}, KernelArguments(a=99), {"a": 99}, None),
        # Merging with a KernelArguments
        ({"b": 2}, KernelArguments(a=1), {"b": 2, "a": 1}, None),
        # Merging execution_settings together
        (
            {"test": "value"},
            KernelArguments(settings=PromptExecutionSettings(service_id="s2")),
            {"test": "value"},
            ["s2"],
        ),
        # Plain dict on the left with KernelArguments+settings on the right
        (
            {"a": 1},
            KernelArguments(b=2, settings=PromptExecutionSettings(service_id="shared")),
            {"a": 1, "b": 2},
            ["shared"],
        ),
        # KernelArguments on both sides with execution_settings
        (
            KernelArguments(a=1, settings=PromptExecutionSettings(service_id="s1")),
            KernelArguments(b=2, settings=PromptExecutionSettings(service_id="s2")),
            {"a": 1, "b": 2},
            ["s1", "s2"],
        ),
        # Same service_id is overwritten by RHS (KernelArguments)
        (
            KernelArguments(a=1, settings=PromptExecutionSettings(service_id="shared")),
            KernelArguments(b=2, settings=PromptExecutionSettings(service_id="shared")),
            {"a": 1, "b": 2},
            ["shared"],
        ),
    ],
)
def test_kernel_arguments_ror_operator(rhs, lhs, expected_dict, expected_settings_keys):
    """Test the __ror__ operator (lhs | rhs) with various argument combinations."""
    result = rhs | lhs
    assert isinstance(result, KernelArguments)
    assert dict(result) == expected_dict
    if expected_settings_keys is None:
        assert result.execution_settings is None
    else:
        assert sorted(result.execution_settings.keys()) == sorted(expected_settings_keys)


@pytest.mark.parametrize("lhs", [42, "foo", None])
def test_kernel_arguments_ror_operator_with_invalid_type(lhs):
    """Test the __ror__ operator with an invalid type raises TypeError."""
    with pytest.raises(TypeError):
        lhs | KernelArguments()
