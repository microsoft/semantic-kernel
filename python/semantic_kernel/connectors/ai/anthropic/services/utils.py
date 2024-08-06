# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import Enum
from typing import Literal

from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason

logger: logging.Logger = logging.getLogger(__name__)


class AnthropicFinishReason(str, Enum):
    """Finish reasons for Anthropic API."""

    END = "end_turn"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    TOOL_USE = "tool_use" 


def finish_reason_from_anthropic_to_semantic_kernel(
    finish_reason: Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"] | None,
) -> SemanticKernelFinishReason | None:
    """Convert a Anthropic FinishReason to a Semantic Kernel FinishReason.

    This is best effort and may not cover all cases as the enums are not identical.
    """
    if finish_reason == AnthropicFinishReason.END:
        return SemanticKernelFinishReason.STOP
    if finish_reason == AnthropicFinishReason.MAX_TOKENS:
        return SemanticKernelFinishReason.LENGTH
    if finish_reason == AnthropicFinishReason.TOOL_USE:
        return SemanticKernelFinishReason.TOOL_CALLS

    return None
