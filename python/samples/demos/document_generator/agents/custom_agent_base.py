# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC
from collections.abc import AsyncIterable, Awaitable, Callable
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.utils.author_role import AuthorRole

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.agents import AgentResponseItem, AgentThread


class Services(str, Enum):
    """Enum for supported chat completion services.

    For service specific settings, refer to this documentation:
    https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion
    """

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"


class CustomAgentBase(ChatCompletionAgent, ABC):
    def _create_ai_service(
        self, service: Services = Services.AZURE_OPENAI, instruction_role: Literal["system", "developer"] = "system"
    ) -> ChatCompletionClientBase:
        """Create an AI service for the agent.

        Note: if using Azure OpenAI, ensure the following environment variables are present in your .env file:
        - AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
        - AZURE_OPENAI_ENDPOINT
        - AZURE_OPENAI_API_KEY (if using Azure OpenAI API key authentication)
        - AZURE_OPENAI_API_VERSION

        If using OpenAI, ensure the following environment variables are present in your .env file:
        - OPENAI_API_KEY
        - OPENAI_CHAT_MODEL_ID

        Args:
            service (Services): The AI service to use.
            instruction_role (str): The role of the instruction in the chat completion request.
                Can be either "system" or "developer". Defaults to "system".

        Returns:
            ChatCompletionClientBase: The AI service instance.

        """

        match service:
            case Services.AZURE_OPENAI:
                from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

                return AzureChatCompletion(instruction_role=instruction_role)
            case Services.OPENAI:
                from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

                return OpenAIChatCompletion(instruction_role=instruction_role)
            case _:
                raise ValueError(
                    f"Unsupported service: {service}. Supported services are: {', '.join([s.value for s in Services])}"
                )

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: "AgentThread | None" = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        additional_user_message: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["AgentResponseItem[ChatMessageContent]"]:
        normalized_messages = self._normalize_messages(messages)

        if additional_user_message:
            normalized_messages.append(ChatMessageContent(role=AuthorRole.USER, content=additional_user_message))

        # Filter out empty or function-only messages to avoid polluting context
        messages_to_pass = [m for m in normalized_messages if m.content]

        async for response in super().invoke(
            messages=messages_to_pass,  # type: ignore
            thread=thread,
            on_intermediate_message=on_intermediate_message,
            arguments=arguments,
            kernel=kernel,
            **kwargs,
        ):
            yield response

    def _normalize_messages(
        self, messages: str | ChatMessageContent | list[str | ChatMessageContent] | None
    ) -> list[ChatMessageContent]:
        if messages is None:
            return []
        if isinstance(messages, (str, ChatMessageContent)):
            messages = [messages]
        normalized: list[ChatMessageContent] = []
        for msg in messages:
            if isinstance(msg, str):
                normalized.append(ChatMessageContent(role=AuthorRole.USER, content=msg))
            else:
                normalized.append(msg)
        return normalized
