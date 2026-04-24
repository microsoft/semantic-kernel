# Copyright (c) Microsoft. All rights reserved.

"""Tests for function_copy metadata copy behavior."""

from unittest.mock import patch

import pytest

from semantic_kernel.functions import kernel_function


@pytest.fixture
def sample_function():
    @kernel_function
    def test_func(input: str) -> str:
        return f"Result: {input}"

    from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod

    return KernelFunctionFromMethod(method=test_func, plugin_name="test_plugin")


class TestFunctionCopyOptimization:
    """Test suite for function_copy metadata isolation."""

    def test_function_copy_same_plugin_creates_independent_metadata(self, sample_function):
        """Test that function_copy isolates metadata even when plugin_name is unchanged."""
        original_plugin = sample_function.plugin_name

        # Case 1: No plugin_name provided (metadata should still be copied)
        copy1 = sample_function.function_copy()
        assert copy1.metadata is not sample_function.metadata
        assert copy1.plugin_name == original_plugin

        # Case 2: Same plugin_name explicitly provided (metadata should still be copied)
        copy2 = sample_function.function_copy(original_plugin)
        assert copy2.metadata is not sample_function.metadata
        assert copy2.plugin_name == original_plugin

    def test_function_copy_different_plugin_creates_copy(self, sample_function):
        """Test that function_copy does create a shallow copy when plugin_name changes.

        This tests that when we actually need to change the plugin_name,
        a shallow copy is created.
        """
        new_plugin_name = "new_plugin"
        copy = sample_function.function_copy(new_plugin_name)

        # Metadata should be different object (copied)
        assert copy.metadata is not sample_function.metadata
        # But should have the new plugin_name
        assert copy.metadata.plugin_name == new_plugin_name
        # Original should be unchanged
        assert sample_function.metadata.plugin_name != new_plugin_name

    def test_function_copy_preserves_function_behavior(self, sample_function):
        """Test that copied function still works correctly."""
        copy = sample_function.function_copy()

        # Verify function metadata is preserved
        assert copy.name == sample_function.name
        assert copy.description == sample_function.description
        # Verify function is callable (indirectly through having same underlying function)
        assert hasattr(copy, "invoke")

    @patch(
        "semantic_kernel.functions.kernel_function.deepcopy",
        side_effect=AssertionError("deepcopy should not be called"),
    )
    def test_function_copy_no_module_deepcopy_usage(self, mock_deepcopy, sample_function):
        """Test that function_copy does not call the module-level deepcopy helper."""
        original_metadata = sample_function.metadata
        copy = sample_function.function_copy()

        assert copy.metadata is not original_metadata
        mock_deepcopy.assert_not_called()

    def test_function_copy_multiple_calls_same_plugin_are_isolated(self, sample_function):
        """Test that multiple copies with same plugin keep independent metadata."""
        copy1 = sample_function.function_copy()
        copy2 = sample_function.function_copy()
        copy3 = sample_function.function_copy(sample_function.plugin_name)

        assert copy1.metadata is not sample_function.metadata
        assert copy2.metadata is not sample_function.metadata
        assert copy3.metadata is not sample_function.metadata
        assert copy1.metadata is not copy2.metadata
        assert copy2.metadata is not copy3.metadata
        assert copy1.metadata is not copy3.metadata
