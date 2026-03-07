# Copyright (c) Microsoft. All rights reserved.

"""Tests for KernelArguments merge optimization (Issue #2: Lazy dict copy)."""

import pytest
from unittest.mock import patch, MagicMock

from semantic_kernel.functions.kernel_arguments import KernelArguments


class TestKernelArgumentsMergeOptimization:
    """Test suite for KernelArguments merge operator optimization."""
    
    def test_or_operator_no_execution_settings_copy(self):
        """Test that | operator doesn't copy when execution_settings is None or empty.
        
        This tests the optimization where dict copy is avoided when not needed.
        """
        args = KernelArguments(a=1, b=2)
        args.execution_settings = None
        
        result = args | {"c": 3}
        
        # Result should have merged values
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] == 3
    
    def test_or_operator_with_kernel_arguments_merge(self):
        """Test | operator with another KernelArguments with execution_settings."""
        settings1 = {"model": "gpt-4", "temperature": 0.7}
        settings2 = {"temperature": 0.9, "max_tokens": 100}
        
        args1 = KernelArguments(a=1, settings=settings1)
        args2 = KernelArguments(b=2, settings=settings2)
        
        result = args1 | args2
        
        # Check merged arguments
        assert result["a"] == 1
        assert result["b"] == 2
        
        # Check merged execution settings
        assert result.execution_settings["model"] == "gpt-4"
        assert result.execution_settings["temperature"] == 0.9  # args2 overwrites
        assert result.execution_settings["max_tokens"] == 100
    
    def test_ror_operator_lazy_copy(self):
        """Test reverse | operator avoids copy when execution_settings is empty."""
        args = KernelArguments(a=1, b=2)
        args.execution_settings = {}
        
        result = {"c": 3} | args
        
        # Result should have merged values
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] == 3
    
    def test_ior_operator_lazy_copy(self):
        """Test in-place |= operator avoids copy when execution_settings exists."""
        settings1 = {"model": "gpt-4", "temperature": 0.7}
        args1 = KernelArguments(a=1, settings=settings1)
        
        settings2 = {"temperature": 0.9}
        args2 = KernelArguments(b=2, settings=settings2)
        
        args1 |= args2
        
        # Check merged in-place
        assert args1["a"] == 1
        assert args1["b"] == 2
        
        # Check in-place merge of settings
        assert args1.execution_settings["model"] == "gpt-4"
        assert args1.execution_settings["temperature"] == 0.9
    
    def test_ior_operator_creates_copy_when_needed(self):
        """Test that |= creates new dict only when target has no execution_settings."""
        args1 = KernelArguments(a=1)
        args1.execution_settings = None
        
        settings2 = {"model": "gpt-4"}
        args2 = KernelArguments(b=2, settings=settings2)
        
        args1 |= args2
        
        # Should have new execution_settings dict
        assert args1.execution_settings is not None
        assert args1.execution_settings["model"] == "gpt-4"
        # Should not be the same reference (it's a copy)
        assert args1.execution_settings is not args2.execution_settings
    
    def test_or_operator_preserves_original_settings(self):
        """Test that | operator doesn't mutate original execution_settings."""
        original_settings = {"model": "gpt-4", "temperature": 0.7}
        args1 = KernelArguments(a=1, settings=original_settings.copy())
        args2 = KernelArguments(b=2, settings={"temperature": 0.9})
        
        result = args1 | args2
        
        # Original args1 settings should be unchanged
        assert args1.execution_settings["temperature"] == 0.7
        # Result should have merged settings
        assert result.execution_settings["temperature"] == 0.9
    
    def test_ior_operator_merges_into_existing_dict(self):
        """Test that |= merges into existing settings dict when present."""
        settings1 = {"model": "gpt-4", "temperature": 0.7}
        args1 = KernelArguments(a=1, settings=settings1)
        original_dict = args1.execution_settings
        
        settings2 = {"temperature": 0.9, "max_tokens": 100}
        args2 = KernelArguments(b=2, settings=settings2)
        
        args1 |= args2
        
        # Should have reused and updated the original dict
        assert args1.execution_settings is original_dict
        assert args1.execution_settings["temperature"] == 0.9
        assert args1.execution_settings["max_tokens"] == 100
