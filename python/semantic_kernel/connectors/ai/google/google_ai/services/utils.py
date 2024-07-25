# Copyright (c) Microsoft. All rights reserved.

import logging

from google.generativeai.protos import Blob, Candidate, Part

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError

logger: logging.Logger = logging.getLogger(__name__)


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


def filter_system_message(chat_history: ChatHistory) -> str | None:
    """Filter the first system message from the chat history.

    If there are multiple system messages, raise an error.
    If there are no system messages, return None.
    """
    if len([message for message in chat_history if message.role == AuthorRole.SYSTEM]) > 1:
        raise ServiceInvalidRequestError(
            "Multiple system messages in chat history. Only one system message is expected."
        )

    for message in chat_history:
        if message.role == AuthorRole.SYSTEM:
            return message.content

    return None


def format_user_message(message: ChatMessageContent) -> list[Part]:
    """Format a user message to the expected object for the client.

    Args:
        message: The user message.

    Returns:
        The formatted user message as a list of parts.
    """
    if not any(isinstance(item, (ImageContent)) for item in message.items):
        return [Part(text=message.content)]

    parts: list[Part] = []
    for item in message.items:
        if isinstance(item, TextContent):
            parts.append(Part(text=message.content))
        elif isinstance(item, ImageContent):
            if item.data_uri:
                parts.append(Part(inline_data=Blob(mime_type=item.mime_type, data=item.data)))
            else:
                # The Google AI API doesn't support image from an arbitrary URI:
                # https://github.com/google-gemini/generative-ai-python/issues/357
                raise ServiceInvalidRequestError(
                    "ImageContent without data_uri in User message while formatting chat history for Google AI"
                )
        else:
            raise ServiceInvalidRequestError(
                "Unsupported item type in User message while formatting chat history for Google AI"
                f" Inference: {type(item)}"
            )

    return parts


def format_assistant_message(message: ChatMessageContent) -> list[Part]:
    """Format an assistant message to the expected object for the client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message as a list of parts.
    """
    return [Part(text=message.content)]
