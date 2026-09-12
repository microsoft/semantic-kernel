# Copyright (c) Microsoft. All rights reserved.

"""Tests for KernelArguments merge operator behavior."""

import pytest

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments


@pytest.fixture
def settings_svc1():
    return PromptExecutionSettings(service_id="service1")


@pytest.fixture
def settings_svc2():
    return PromptExecutionSettings(service_id="service2")


@pytest.fixture
def settings_default():
    return PromptExecutionSettings(service_id="default")


class TestKernelArgumentsMergeOptimization:
    """Test suite for KernelArguments merge operator behavior."""

    def test_or_operator_no_execution_settings(self):
        """Test that | operator works when execution_settings is None."""
        args = KernelArguments(a=1, b=2)

        result = args | {"c": 3}

        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] == 3

    def test_or_operator_merges_settings_by_service_id(self, settings_svc1, settings_svc2):
        """Test | merges execution_settings keyed by service_id."""
        args1 = KernelArguments(a=1, settings=settings_svc1)
        args2 = KernelArguments(b=2, settings=settings_svc2)

        result = args1 | args2

        assert result["a"] == 1
        assert result["b"] == 2
        assert result.execution_settings["service1"] is settings_svc1
        assert result.execution_settings["service2"] is settings_svc2

    def test_or_operator_right_side_wins_on_same_service_id(self, settings_default):
        """Test | overwrites execution_settings when both sides share a service_id."""
        settings_override = PromptExecutionSettings(service_id="default")
        args1 = KernelArguments(a=1, settings=settings_default)
        args2 = KernelArguments(b=2, settings=settings_override)

        result = args1 | args2

        assert result.execution_settings["default"] is settings_override

    def test_ror_operator_merges_plain_dict_with_kernel_arguments(self, settings_svc1):
        """Test reverse | operator merges a plain dict with KernelArguments."""
        args = KernelArguments(a=1, settings=settings_svc1)

        result = {"b": 2} | args

        assert result["a"] == 1
        assert result["b"] == 2
        assert result.execution_settings["service1"] is settings_svc1

    def test_ior_operator_merges_settings_in_place(self, settings_svc1, settings_svc2):
        """Test |= merges execution_settings into the existing dict in-place."""
        args1 = KernelArguments(a=1, settings=settings_svc1)
        original_dict = args1.execution_settings

        args2 = KernelArguments(b=2, settings=settings_svc2)
        args1 |= args2

        assert args1["a"] == 1
        assert args1["b"] == 2
        assert args1.execution_settings is original_dict
        assert args1.execution_settings["service1"] is settings_svc1
        assert args1.execution_settings["service2"] is settings_svc2

    def test_ior_operator_copies_settings_when_target_has_none(self, settings_svc1):
        """Test |= creates a copy of execution_settings when target has none."""
        args1 = KernelArguments(a=1)
        assert args1.execution_settings is None

        args2 = KernelArguments(b=2, settings=settings_svc1)
        args1 |= args2

        assert args1.execution_settings is not None
        assert args1.execution_settings["service1"] is settings_svc1
        assert args1.execution_settings is not args2.execution_settings

    def test_or_operator_does_not_mutate_original_settings(self, settings_svc1, settings_svc2):
        """Test that | does not mutate the original execution_settings."""
        args1 = KernelArguments(a=1, settings=settings_svc1)
        args2 = KernelArguments(b=2, settings=settings_svc2)
        original_settings = args1.execution_settings

        result = args1 | args2

        assert args1.execution_settings is original_settings
        assert "service2" not in args1.execution_settings
        assert "service2" in result.execution_settings

    def test_ior_operator_right_side_wins_on_same_service_id(self, settings_default):
        """Test |= overwrites existing settings entry when service_id matches."""
        settings_override = PromptExecutionSettings(service_id="default")
        args1 = KernelArguments(a=1, settings=settings_default)
        args2 = KernelArguments(b=2, settings=settings_override)

        args1 |= args2

        assert args1.execution_settings["default"] is settings_override
