"""Class to hold chat messages."""
from typing import List, Optional

from semantic_kernel.models.completion_content import CompletionContent
from semantic_kernel.models.completion_result_base import CompletionResultBase


class CompletionResult(CompletionResultBase):
    """Class to hold text completion results."""

    @property
    def content(self) -> Optional[str]:
        """Return the content of the first choice returned by the API."""
        return self.choices[0].text

    @classmethod
    def from_chunk_list(
        cls, chunk_list: List["CompletionResultBase"]
    ) -> "CompletionResultBase":
        """Parse a list of CompletionResults with texts into a CompletionResult."""
        completion_id = chunk_list[0].id
        created = chunk_list[0].created
        object_type = "text_completion"
        model = chunk_list[0].model
        usage = None
        choices = {}
        for chunk in chunk_list:
            usage = chunk.usage if chunk.usage else usage
            completion_id = chunk.id if chunk.id else completion_id
            created = chunk.created if chunk.created else created
            model = chunk.model if chunk.model else model
            for choice in chunk.choices:
                if choice.index in choices:
                    if choice.finish_reason:
                        choices[choice.index].finish_reason = choice.finish_reason
                    if choice.text:
                        choices[choice.index].text += choice.text
                    # TODO: deal with logprobs
                    # if choice.delta.logprobs:
                    #     choices[choice.index].logprobs = choice.delta.logprobs
                else:
                    choices[choice.index] = CompletionContent(
                        index=choice.index,
                        text=choice.text,
                        finish_reason=choice.finish_reason,
                        logprobs=choice.logprobs,
                    )
        return cls(
            id=completion_id,
            object_type=object_type,
            created=created,
            model=model,
            choices=list(choices.values()),
            usage=usage,
            is_streaming_result=False,
        )
