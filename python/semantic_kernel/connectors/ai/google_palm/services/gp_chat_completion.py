# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, Dict, List, Optional, Tuple

from semantic_kernel.models.contents.chat_message_content import ChatMessageContent
from semantic_kernel.models.contents.text_content import TextContent

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import google.generativeai as palm
from google.generativeai.types import ChatResponse, MessageDict
from pydantic import PrivateAttr, StringConstraints

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import (
    GooglePalmChatPromptExecutionSettings,
    GooglePalmPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class GooglePalmChatCompletion(ChatCompletionClientBase, TextCompletionClientBase, AIServiceClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    _message_history: Optional[ChatResponse] = PrivateAttr()

    def __init__(
        self,
        ai_model_id: str,
        api_key: str,
        message_history: Optional[ChatResponse] = None,
        log: Optional[Any] = None,
    ):
        """
        Initializes a new instance of the GooglePalmChatCompletion class.

        Arguments:
            ai_model_id {str} -- GooglePalm model name, see
                https://developers.generativeai.google/models/language
            api_key {str} -- GooglePalm API key, see
                https://developers.generativeai.google/products/palm
            message_history {Optional[ChatResponse]} -- The message history to use for context. (Optional)
            log {Optional[Any]} -- A logger to use for logging. (Optional)
        """
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
        )
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        self._message_history = message_history

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        settings: GooglePalmPromptExecutionSettings,
    ) -> List[ChatMessageContent]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings {GooglePalmPromptExecutionSettings} -- Settings for the request.

        Returns:
            List[ChatMessageContent] -- A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        settings.messages = [{"author": message["role"], "content": message["content"]} for message in messages]
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_chat_request(settings)
        return [
            self._create_chat_message_content(response, candidate, index)
            for index, candidate in enumerate(response.candidates)
        ]

    def _create_chat_message_content(
        self, response: ChatResponse, candidate: MessageDict, index: int
    ) -> ChatMessageContent:
        """Create a chat message content object from a response.

        Arguments:
            response {ChatResponse} -- The response to create the content from.

        Returns:
            ChatMessageContent -- The created chat message content.
        """
        metadata = {"citation_metadata": candidate.get("citation_metadata"), "filters": response.filters}
        return ChatMessageContent(
            choice_index=index,
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=candidate.get("author"),
            content=candidate.get("content"),
        )

    async def complete_chat_stream(
        self,
        messages: List[Tuple[str, str]],
        settings: GooglePalmPromptExecutionSettings,
    ):
        raise NotImplementedError("Google Palm API does not currently support streaming")

    async def complete(
        self,
        prompt: str,
        settings: GooglePalmPromptExecutionSettings,
        **kwargs,
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {GooglePalmPromptExecutionSettings} -- Settings for the request.

        Returns:
            List[TextContent] -- A list of TextContent objects representing the response(s) from the LLM.
        """
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        settings.messages = [{"author": "user", "content": prompt}]
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_chat_request(settings)

        return [self._create_text_content(response, candidate) for candidate in response.candidates]

    def _create_text_content(self, response: ChatResponse, candidate: MessageDict) -> TextContent:
        """Create a text content object from a response.

        Arguments:
            response {ChatResponse} -- The response to create the content from.

        Returns:
            TextContent -- The created text content.
        """
        metadata = {"citation_metadata": candidate.get("citation_metadata"), "filters": response.filters}
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            text=candidate.get("content"),
        )

    async def complete_stream(
        self,
        prompt: str,
        settings: GooglePalmPromptExecutionSettings,
        **kwargs,
    ):
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        raise NotImplementedError("Google Palm API does not currently support streaming")

    async def _send_chat_request(
        self,
        settings: GooglePalmPromptExecutionSettings,
    ):
        """
        Completes the given user message. If len(messages) > 1, and a
        conversation has not been initiated yet, it is assumed that chat history
        is needed for context. All messages preceding the last message will be
        utilized for context. This also enables Google PaLM to utilize memory
        and plugins, which should be stored in the messages parameter as system
        messages.

        Arguments:
            messages {str} -- The message (from a user) to respond to.
            settings {GooglePalmPromptExecutionSettings} -- The request settings.
            context {str} -- Text that should be provided to the model first,
            to ground the response. If a system message is provided, it will be
            used as context.
            examples {ExamplesOptions} -- 	Examples of what the model should
            generate. This includes both the user input and the response that
            the model should emulate. These examples are treated identically to
            conversation messages except that they take precedence over the
            history in messages: If the total input size exceeds the model's
            input_token_limit the input will be truncated. Items will be dropped
            from messages before examples
            See: https://developers.generativeai.google/api/python/google/generativeai/types/ExampleOptions
            prompt {MessagePromptOptions} -- 	You may pass a
            types.MessagePromptOptions instead of a setting context/examples/messages,
            but not both.
            See: https://developers.generativeai.google/api/python/google/generativeai/types/MessagePromptOptions

        Returns:
            str -- The completed text.
        """
        if settings is None:
            raise ValueError("The request settings cannot be `None`")

        if settings.messages[-1]["author"] != "user":
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The last message must be from the user",
            )
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        try:
            if self._message_history is None:
                response = palm.chat(**settings.prepare_settings_dict())  # Start a new conversation
            else:
                response = self._message_history.reply(  # Continue the conversation
                    settings.messages[-1]["content"],
                )
            self._message_history = response  # Store response object for future use
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        return response

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return GooglePalmChatPromptExecutionSettings
