# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import Enum

from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason

logger: logging.Logger = logging.getLogger(__name__)


class AnthropicFinishReason(str, Enum):
    """Finish reasons for Anthropic API."""

    END = "end_turn"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    TOOL_USE = "tool_use" 


# map finish reasons from Anthropic to Semantic Kernel
ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP = {
    AnthropicFinishReason.END: SemanticKernelFinishReason.STOP,
    AnthropicFinishReason.MAX_TOKENS: SemanticKernelFinishReason.LENGTH,
    AnthropicFinishReason.TOOL_USE: SemanticKernelFinishReason.TOOL_CALLS,
}
