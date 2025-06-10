# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage


def test_completion_usage() -> None:
    """Test the CompletionUsage class."""
    # Create a CompletionUsage object
    usage = CompletionUsage(prompt_tokens=10, completion_tokens=20)

    # Check that the prompt tokens and completion tokens are set correctly
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20

    # Create another CompletionUsage object
    other_usage = CompletionUsage(prompt_tokens=5, completion_tokens=15)

    # Add the two CompletionUsage objects together
    total_usage = usage + other_usage

    # Check that the total prompt tokens and completion tokens are correct
    assert total_usage.prompt_tokens == 15
    assert total_usage.completion_tokens == 35


def test_completion_usage_empty() -> None:
    """Test the CompletionUsage class with empty values."""
    # Create a CompletionUsage object with empty values
    usage = CompletionUsage()

    # Check that the prompt tokens and completion tokens are None
    assert usage.prompt_tokens is None
    assert usage.completion_tokens is None

    # Create another CompletionUsage object with empty values
    other_usage = CompletionUsage(prompt_tokens=5, completion_tokens=None)

    # Add the two CompletionUsage objects together
    total_usage = usage + other_usage

    # Check that the total prompt tokens and completion tokens are None
    assert total_usage.prompt_tokens == 5
    assert total_usage.completion_tokens == 0
