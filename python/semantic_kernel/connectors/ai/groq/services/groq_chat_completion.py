# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from groq import AsyncGroq
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.groq.services.groq_base import GroqBase
from semantic_kernel.connectors.ai.groq.settings.groq_settings import GroqSettings
from semantic_kernel.connectors.ai.groq.settings.prompt_execution_settings import GroqChatPromptExecutionSettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_chat_completion

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


class GroqChatCompletion(GroqBase, ChatCompletionClientBase):
    """Initializes a new instance of the GroqChatCompletion class."""

    def __init__(
        self,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        client: AsyncGroq | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize a GroqChatCompletion service.

        Args:
            service_id (Optional[str]): Service ID tied to the execution settings. (Optional)
            ai_model_id (Optional[str]): The model name. (Optional)
            client (Optional[AsyncGroq]): A custom Groq client to use for the service. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        """
        try:
            groq_settings = GroqSettings.create(
                model=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Groq settings.", ex) from ex

        super().__init__(
            service_id=service_id or groq_settings.model,
            ai_model_id=groq_settings.chat_model_id,
            client=client or AsyncGroq(),
        )

    @override
    @trace_chat_completion(GroqBase.MODEL_PROVIDER_NAME)
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        """This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat.completions.create(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=False,
            **settings.prepare_settings_dict(),
        )

        return [
            ChatMessageContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                role=AuthorRole.ASSISTANT,
                content=response_object.choices[0].message.content,
            )
        ]

    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Streams a text completion using a Groq model.

        Note that this method does not support multiple responses.

        Args:
            chat_history (ChatHistory): A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings (PromptExecutionSettings): Request settings.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: Stream of StreamingChatMessageContent objects.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat.completions.create(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=True,
            **settings.prepare_settings_dict(),
        )

        async for part in response_object:
            yield [
                StreamingChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    content=part.choices[0].delta.content,
                )
            ]

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return GroqChatPromptExecutionSettings
