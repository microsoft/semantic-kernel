# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


class ChatCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for chat completion AI services."""

    @abstractmethod
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Create chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chats in a chat_history object, that can be
                rendered into messages from system, user, assistant and tools.
            settings (PromptExecutionSettings): Settings for the request.
            **kwargs (Any): The optional arguments.

        Returns:
            A list of chat message contents representing the response(s) from the LLM.
        """
        pass

    async def get_chat_message_content(
        self, chat_history: "ChatHistory", settings: "PromptExecutionSettings", **kwargs: Any
    ) -> "ChatMessageContent | None":
        """This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            A string representing the response from the LLM.
        """
        results = await self.get_chat_message_contents(chat_history=chat_history, settings=settings, **kwargs)
        if results:
            return results[0]
        # this should not happen, should error out before returning an empty list
        return None  # pragma: no cover

    @abstractmethod
    def get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Create streaming chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        ...

    async def get_streaming_chat_message_content(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator["StreamingChatMessageContent | None", Any]:
        """This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        async for streaming_chat_message_contents in self.get_streaming_chat_message_contents(
            chat_history, settings, **kwargs
        ):
            if streaming_chat_message_contents:
                yield streaming_chat_message_contents[0]
            else:
                # this should not happen, should error out before returning an empty list
                yield None  # pragma: no cover

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        """Prepare the chat history for a request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        ChatRole.TOOL messages need to be formatted different than system/user/assistant messages:
            They require a "tool_call_id" and (function) "name" key, and the "metadata" key should
            be removed. The "encoding" key should also be removed.

        Override this method to customize the formatting of the chat history for a request.

        Args:
            chat_history (ChatHistory): The chat history to prepare.
            role_key (str): The key name for the role/author.
            content_key (str): The key name for the content/message.

        Returns:
            prepared_chat_history (Any): The prepared chat history for a request.
        """
        return [message.to_dict(role_key=role_key, content_key=content_key) for message in chat_history.messages]
