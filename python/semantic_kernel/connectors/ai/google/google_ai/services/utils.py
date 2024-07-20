# Copyright (c) Microsoft. All rights reserved.

from google.generativeai.protos import Candidate

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason


def finish_reason_from_google_ai_to_semantic_kernel(
    finish_reason: Candidate.FinishReason,
) -> SemanticKernelFinishReason | None:
    """Convert a Google AI FinishReason to a Semantic Kernel FinishReason.

    This is best effort and may not cover all cases as the enums are not identical.
    """
    if finish_reason == Candidate.FinishReason.STOP:
        return SemanticKernelFinishReason.STOP

    if finish_reason == Candidate.FinishReason.MAX_TOKENS:
        return SemanticKernelFinishReason.LENGTH

    if finish_reason == Candidate.FinishReason.SAFETY:
        return SemanticKernelFinishReason.CONTENT_FILTER

    return None


def filter_first_system_message(chat_history: ChatHistory) -> str | None:
    """Filter the first system message from the chat history.

    If there are no system messages, return None.
    """
    for message in chat_history:
        if message.role == AuthorRole.SYSTEM:
            return message.content

    return None
