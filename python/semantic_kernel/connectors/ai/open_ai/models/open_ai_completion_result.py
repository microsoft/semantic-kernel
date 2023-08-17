"""Class to hold chat messages."""

from openai.openai_object import OpenAIObject

from semantic_kernel.models.completion_content import (
    CompletionContent,
)
from semantic_kernel.models.completion_result import (
    CompletionResult,
)
from semantic_kernel.models.finish_reason import (
    FinishReason,
)
from semantic_kernel.models.usage_result import UsageResult


class OpenAICompletionResult(CompletionResult):
    """Open AI API specific ChatCompletionResult."""

    @classmethod
    def from_openai_object(
        cls, openai_object: OpenAIObject, is_streaming: bool = False
    ) -> CompletionResult:
        """Parse a OpenAI Object response into a ChatCompletionResult."""
        choices = None
        if len(openai_object.choices) > 0:
            choices = [
                CompletionContent(
                    index=x.index,
                    text=x.text,
                    finish_reason=FinishReason(x.finish_reason)
                    if x.finish_reason
                    else None,
                    logprobs=x.logprobs,
                )
                for x in openai_object.choices
            ]
        usage = None
        if openai_object.usage:
            usage = UsageResult(
                prompt_tokens=openai_object.usage.prompt_tokens,
                completion_tokens=openai_object.usage.completion_tokens,
                total_tokens=openai_object.usage.total_tokens,
            )
        return cls(
            id=openai_object.id,
            object_type=openai_object.object,
            created=openai_object.created,
            model=openai_object.model,
            choices=choices,
            usage=usage,
            is_streaming_result=is_streaming,
        )
