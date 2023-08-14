"""Class to hold completion content."""
from typing import Optional

from semantic_kernel.models.completion_content_base import CompletionContentBase


class CompletionContent(CompletionContentBase):
    logprobs: Optional[dict]
    text: Optional[str]
