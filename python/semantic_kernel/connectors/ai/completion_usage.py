# Copyright (c) Microsoft. All rights reserved.


from openai.types import CompletionUsage as OpenAICompletionUsage
from openai.types.completion_usage import CompletionTokensDetails, PromptTokensDetails

from semantic_kernel.kernel_pydantic import KernelBaseModel


class CompletionUsage(KernelBaseModel):
    """A class representing the usage of tokens in a completion request."""

    prompt_tokens: int | None = None
    prompt_tokens_details: PromptTokensDetails | None = None
    completion_tokens: int | None = None
    completion_tokens_details: CompletionTokensDetails | None = None

    @classmethod
    def from_openai(cls, openai_completion_usage: OpenAICompletionUsage):
        """Create a CompletionUsage instance from an OpenAICompletionUsage instance."""
        return cls(
            prompt_tokens=openai_completion_usage.prompt_tokens,
            prompt_tokens_details=openai_completion_usage.prompt_tokens_details
            if openai_completion_usage.prompt_tokens_details
            else None,
            completion_tokens=openai_completion_usage.completion_tokens,
            completion_tokens_details=openai_completion_usage.completion_tokens_details
            if openai_completion_usage.completion_tokens_details
            else None,
        )

    def __add__(self, other: "CompletionUsage") -> "CompletionUsage":
        """Combine two CompletionUsage instances by summing their token counts."""

        def _merge_details(cls, a, b):
            """Merge two details objects by summing their fields."""
            if a is None and b is None:
                return None
            kwargs = {}
            for field in cls.__annotations__:
                x = getattr(a, field, None)
                y = getattr(b, field, None)
                value = None if x is None and y is None else (x or 0) + (y or 0)
                kwargs[field] = value
            return cls(**kwargs)

        return CompletionUsage(
            prompt_tokens=(self.prompt_tokens or 0) + (other.prompt_tokens or 0),
            completion_tokens=(self.completion_tokens or 0) + (other.completion_tokens or 0),
            prompt_tokens_details=_merge_details(
                PromptTokensDetails, self.prompt_tokens_details, other.prompt_tokens_details
            ),
            completion_tokens_details=_merge_details(
                CompletionTokensDetails, self.completion_tokens_details, other.completion_tokens_details
            ),
        )
