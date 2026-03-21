# Copyright (c) Microsoft. All rights reserved.

"""Tests for function_copy optimization (Issue #1: Lazy deepcopy)."""

import pytest
from unittest.mock import patch

from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions import kernel_function


@pytest.fixture
def sample_function():
    """Create a sample kernel function for testing."""
    @kernel_function
    def test_func(input: str) -> str:
        return f"Result: {input}"
    
    return test_func


class TestFunctionCopyOptimization:
    """Test suite for function_copy lazy deepcopy optimization."""
    
    def test_function_copy_same_plugin_no_deepcopy(self, sample_function):
        """Test that function_copy doesn't deepcopy when plugin_name is same or None.
        
        This tests the optimization where metadata is reused when no plugin_name change.
        """
        original_plugin = sample_function.plugin_name
        
        # Case 1: No plugin_name provided (should reuse reference)
        copy1 = sample_function.function_copy()
        assert copy1.metadata is sample_function.metadata  # Should be same reference
        assert copy1.plugin_name == original_plugin
        
        # Case 2: Same plugin_name provided (should reuse reference)
        copy2 = sample_function.function_copy(original_plugin)
        assert copy2.metadata is sample_function.metadata  # Should be same reference
    
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
        assert hasattr(copy, 'invoke')
    
    @patch('semantic_kernel.functions.kernel_function.deepcopy', side_effect=AssertionError("deepcopy should not be called"))
    def test_function_copy_no_unnecessary_deepcopy(self, mock_deepcopy, sample_function):
        """Test that deepcopy is NOT called when plugin_name doesn't change.
        
        This is the key optimization test - it verifies that the old problematic
        deepcopy is not being called anymore.
        """
        # When plugin_name is None or same, deepcopy should not be called
        try:
            sample_function.function_copy()
            # If we get here, deepcopy was not called (good!)
            assert True
        except AssertionError as e:
            if "deepcopy should not be called" in str(e):
                pytest.fail("function_copy still calls deepcopy unnecessarily")
            raise
    
    def test_function_copy_multiple_calls_same_plugin(self, sample_function):
        """Test that multiple copies with same plugin reuse metadata.
        
        This tests the performance benefit of reusing metadata references
        when no change is needed.
        """
        copy1 = sample_function.function_copy()
        copy2 = sample_function.function_copy()
        copy3 = sample_function.function_copy(sample_function.plugin_name)
        
        # All should reference the same original metadata
        assert copy1.metadata is sample_function.metadata
        assert copy2.metadata is sample_function.metadata
        assert copy3.metadata is sample_function.metadata
