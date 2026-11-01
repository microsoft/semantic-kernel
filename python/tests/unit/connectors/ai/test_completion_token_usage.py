# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage


def test_completion_usage() -> None:
    """Test the CompletionUsage class."""
    # Create a CompletionUsage object
    usage = CompletionUsage(prompt_tokens=10, completion_tokens=20)

    # Check that the prompt tokens and completion tokens are set correctly
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30

    # Create another CompletionUsage object
    other_usage = CompletionUsage(prompt_tokens=5, completion_tokens=15)

    # Add the two CompletionUsage objects together
    total_usage = usage + other_usage

    # Check that the total prompt tokens and completion tokens are correct
    assert total_usage.prompt_tokens == 15
    assert total_usage.completion_tokens == 35
    assert total_usage.total_tokens == 50


def test_completion_usage_empty() -> None:
    """Test the CompletionUsage class with empty values."""
    # Create a CompletionUsage object with empty values
    usage = CompletionUsage()

    # Check that the prompt tokens and completion tokens are None
    assert usage.prompt_tokens is None
    assert usage.completion_tokens is None
    assert usage.total_tokens == 0

    # Create another CompletionUsage object with empty values
    other_usage = CompletionUsage(prompt_tokens=5, completion_tokens=None)

    # Add the two CompletionUsage objects together
    total_usage = usage + other_usage

    # Check that the total prompt tokens and completion tokens are None
    assert total_usage.prompt_tokens == 5
    assert total_usage.completion_tokens == 0


def test_completion_usage_sum() -> None:
    """Test summing a sequence of CompletionUsage instances with sum()."""
    u1 = CompletionUsage(prompt_tokens=10, completion_tokens=20)
    u2 = CompletionUsage(prompt_tokens=5, completion_tokens=15)
    u3 = CompletionUsage(prompt_tokens=2, completion_tokens=3)

    total = sum([u1, u2, u3])
    assert total.prompt_tokens == 17
    assert total.completion_tokens == 38
    assert total.total_tokens == 55


def test_completion_usage_invalid_add() -> None:
    """Test adding unsupported types raises TypeError."""
    usage = CompletionUsage(prompt_tokens=10, completion_tokens=20)
    with pytest.raises(TypeError):
        _ = usage + 5
