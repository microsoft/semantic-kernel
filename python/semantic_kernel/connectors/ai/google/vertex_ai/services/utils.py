# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from google.cloud.aiplatform_v1beta1.types.content import Blob, Candidate, Part
from google.cloud.aiplatform_v1beta1.types.tool import FunctionCall, FunctionResponse
from vertexai.generative_models import FunctionDeclaration, Tool, ToolConfig

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionCallChoiceConfiguration, FunctionChoiceType
from semantic_kernel.connectors.ai.google.shared_utils import (
    FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
    format_function_result_content_name_to_gemini_function_name,
    format_kernel_function_fully_qualified_name_to_gemini_function_name,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger: logging.Logger = logging.getLogger(__name__)


def finish_reason_from_vertex_ai_to_semantic_kernel(
    finish_reason: Candidate.FinishReason,
) -> SemanticKernelFinishReason | None:
    """Convert a Vertex AI FinishReason to a Semantic Kernel FinishReason.

    This is best effort and may not cover all cases as the enums are not identical.
    """
    if finish_reason == Candidate.FinishReason.STOP:
        return SemanticKernelFinishReason.STOP

    if finish_reason == Candidate.FinishReason.MAX_TOKENS:
        return SemanticKernelFinishReason.LENGTH

    if finish_reason == Candidate.FinishReason.SAFETY:
        return SemanticKernelFinishReason.CONTENT_FILTER

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
                # The Google AI API doesn't support images from arbitrary URIs:
                # https://github.com/google-gemini/generative-ai-python/issues/357
                raise ServiceInvalidRequestError(
                    "ImageContent without data_uri in User message while formatting chat history for Vertex AI"
                )
        else:
            raise ServiceInvalidRequestError(
                "Unsupported item type in User message while formatting chat history for Vertex AI"
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
    text_items: list[TextContent] = []
    function_call_items: list[FunctionCallContent] = []
    for item in message.items:
        if isinstance(item, TextContent):
            text_items.append(item)
        elif isinstance(item, FunctionCallContent):
            function_call_items.append(item)
        else:
            raise ServiceInvalidRequestError(
                "Unsupported item type in Assistant message while formatting chat history for Vertex AI"
                f" Inference: {type(item)}"
            )

    if len(text_items) > 1:
        raise ServiceInvalidRequestError(
            "Unsupported number of text items in Assistant message while formatting chat history for Vertex AI"
            f" Inference: {len(text_items)}"
        )

    if len(function_call_items) > 1:
        raise ServiceInvalidRequestError(
            "Unsupported number of function call items in Assistant message while formatting chat history for Vertex AI"
            f" Inference: {len(function_call_items)}"
        )

    part = Part()
    if text_items:
        part.text = text_items[0].text
    if function_call_items:
        part.function_call = FunctionCall(
            name=function_call_items[0].name,
            args=function_call_items[0].arguments,
        )

    return [part]


def format_tool_message(message: ChatMessageContent) -> list[Part]:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    if len(message.items) != 1:
        logger.warning(
            "Unsupported number of items in Tool message while formatting chat history for Vertex AI: "
            f"{len(message.items)}"
        )

    if not isinstance(message.items[0], FunctionResultContent):
        raise ValueError("No FunctionResultContent found in the message items")

    gemini_function_name = format_function_result_content_name_to_gemini_function_name(message.items[0])

    return [
        Part(
            function_response=FunctionResponse(
                name=gemini_function_name,
                response={
                    "name": gemini_function_name,
                    "content": message.items[0].result,
                },
            ),
        )
    ]


def kernel_function_metadata_to_vertex_ai_function_call_format(metadata: KernelFunctionMetadata) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return FunctionDeclaration(
        name=format_kernel_function_fully_qualified_name_to_gemini_function_name(metadata),
        description=metadata.description or "",
        parameters={
            "type": "object",
            "properties": {param.name: param.schema_data for param in metadata.parameters},
            "required": [p.name for p in metadata.parameters if p.is_required],
        },
    )


def update_settings_from_function_choice_configuration(
    function_choice_configuration: FunctionCallChoiceConfiguration,
    settings: VertexAIChatPromptExecutionSettings,
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if function_choice_configuration.available_functions:
        settings.tool_config = ToolConfig(
            function_calling_config=ToolConfig.FunctionCallingConfig(
                mode=FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[type],
            ),
        )
        settings.tools = [
            Tool(
                function_declarations=[
                    kernel_function_metadata_to_vertex_ai_function_call_format(f)
                    for f in function_choice_configuration.available_functions
                ]
            )
        ]
