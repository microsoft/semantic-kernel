"""Class to hold completion content."""
from typing import Optional

from semantic_kernel.models.finish_reason import (
    FinishReason,
)
from semantic_kernel.sk_pydantic import SKBaseModel


class CompletionContentBase(SKBaseModel):
    index: int
    finish_reason: Optional[FinishReason]
