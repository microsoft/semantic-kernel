"""Class to hold chat messages."""
from typing import List, Optional

from semantic_kernel.models.completion_content_base import (
    CompletionContentBase,
)
from semantic_kernel.models.usage_result import UsageResult
from semantic_kernel.sk_pydantic import SKBaseModel


class CompletionResultBase(SKBaseModel):
    id: Optional[str]
    object_type: Optional[str]
    created: Optional[int]
    model: Optional[str]
    choices: Optional[List[CompletionContentBase]]
    usage: Optional[UsageResult]
    is_streaming_result: Optional[bool] = False

    @property
    def content(self) -> Optional[str]:
        """Return the content of the first choice returned by the API."""
        raise NotImplementedError("content property must be implemented in subclass")

    @classmethod
    def from_chunk_list(
        cls, chunk_list: List["CompletionResultBase"]
    ) -> "CompletionResultBase":
        """Parse a list of CompletionResults with ChunkContent into a CompletionResult."""
        raise NotImplementedError(
            "from_chunk_list method must be implemented in subclass"
        )
