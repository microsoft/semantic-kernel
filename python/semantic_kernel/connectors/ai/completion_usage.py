# Copyright (c) Microsoft. All rights reserved.

from openai.types import CompletionUsage as OpenAICompletionUsage

from semantic_kernel.kernel_pydantic import KernelBaseModel


class CompletionUsage(KernelBaseModel):
    """Completion usage information."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    @classmethod
    def from_openai(cls, openai_completion_usage: OpenAICompletionUsage):
        """Create a CompletionUsage object from an OpenAI response."""
        return cls(
            prompt_tokens=openai_completion_usage.prompt_tokens,
            completion_tokens=openai_completion_usage.completion_tokens,
        )
