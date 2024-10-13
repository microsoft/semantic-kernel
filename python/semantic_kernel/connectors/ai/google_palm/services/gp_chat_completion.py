# Copyright (c) Microsoft. All rights reserved.

import logging
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import Annotated, Any
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
from typing import Annotated, Any
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
from typing import Annotated, Any
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
from typing import Annotated, Any
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
from typing import Annotated, Any
=======
import sys
from typing import Dict, List, Optional, Tuple

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

import google.generativeai as palm
from google.generativeai.types import ChatResponse, MessageDict
from pydantic import PrivateAttr, StringConstraints, ValidationError
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======

<<<<<<< main
>>>>>>> Stashed changes
=======

<<<<<<< main
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import (
    GooglePalmChatPromptExecutionSettings,
    GooglePalmPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google_palm.settings.google_palm_settings import GooglePalmSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError, ServiceResponseException

logger: logging.Logger = logging.getLogger(__name__)

int_to_role = {1: AuthorRole.USER, 2: AuthorRole.SYSTEM, 3: AuthorRole.ASSISTANT, 4: AuthorRole.TOOL}
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======

>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div

>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
=======
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
>>>>>>> ms/small_fixes
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import (
    GooglePalmChatPromptExecutionSettings,
    GooglePalmPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google_palm.settings.google_palm_settings import GooglePalmSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
<<<<<<< main
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError, ServiceResponseException

logger: logging.Logger = logging.getLogger(__name__)

int_to_role = {1: AuthorRole.USER, 2: AuthorRole.SYSTEM, 3: AuthorRole.ASSISTANT, 4: AuthorRole.TOOL}
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head


class GooglePalmChatCompletion(ChatCompletionClientBase, TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    _message_history: ChatHistory | None = PrivateAttr()
    service_id: str | None = None
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_role import ChatRole

logger: logging.Logger = logging.getLogger(__name__)

int_to_role = {1: ChatRole.USER, 2: ChatRole.SYSTEM, 3: ChatRole.ASSISTANT, 4: ChatRole.TOOL}
<<<<<<< div
<<<<<<< div
>>>>>>> origin/main
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head


class GooglePalmChatCompletion(ChatCompletionClientBase, TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    _message_history: ChatHistory | None = PrivateAttr()
    service_id: str | None = None
=======
    _message_history: Optional[ChatHistory] = PrivateAttr()
    service_id: Optional[str] = None
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    _message_history: Optional[ChatHistory] = PrivateAttr()
    service_id: Optional[str] = None
>>>>>>> ms/small_fixes
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    _message_history: Optional[ChatHistory] = PrivateAttr()
    service_id: Optional[str] = None
>>>>>>> ms/small_fixes
>>>>>>> main
=======
>>>>>>> head

    def __init__(
        self,
        ai_model_id: str,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        api_key: str | None = None,
        message_history: ChatHistory | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
=======
        api_key: str,
        message_history: Optional[ChatHistory] = None,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
        api_key: str,
        message_history: Optional[ChatHistory] = None,
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    ):
        """Initializes a new instance of the GooglePalmChatCompletion class.

        Args:
            ai_model_id (str): GooglePalm model name, see
                https://developers.generativeai.google/models/language
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
>>>>>>> head
            api_key (str | None): The optional API key to use. If not provided, will be read from either
                the env vars or the .env settings file
            message_history (ChatHistory | None): The message history to use for context. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)

        Raises:
            ServiceInitializationError: When any of the required settings are missing.
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
            api_key {str} -- GooglePalm API key, see
                https://developers.generativeai.google/products/palm
            message_history {Optional[ChatHistory]} -- The message history to use for context. (Optional)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        """
        try:
            google_palm_settings = GooglePalmSettings.create(
                api_key=api_key,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Google Palm settings", ex) from ex

        if not google_palm_settings.chat_model_id:
            raise ServiceInitializationError("The chat model ID is required for a Chat Completion Model.")

        super().__init__(
            ai_model_id=google_palm_settings.chat_model_id,
            api_key=google_palm_settings.api_key.get_secret_value(),
        )
        self._message_history = message_history

    async def get_chat_message_contents(
        self,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        chat_history: ChatHistory,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        chat_history: ChatHistory,
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        chat_history: ChatHistory,
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        chat_history: ChatHistory,
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        chat_history: ChatHistory,
=======
        messages: ChatHistory,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        settings: GooglePalmPromptExecutionSettings,
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        """This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Args:
            chat_history (List[ChatMessage]): A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings (GooglePalmPromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        settings.messages = self._prepare_chat_history_for_request(chat_history, role_key="author")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        settings.messages = self._prepare_chat_history_for_request(chat_history, role_key="author")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        settings.messages = self._prepare_chat_history_for_request(chat_history, role_key="author")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        settings.messages = self._prepare_chat_history_for_request(chat_history, role_key="author")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        settings.messages = self._prepare_chat_history_for_request(chat_history, role_key="author")
=======
        settings.messages = self._prepare_chat_history_for_request(messages)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
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

        Args:
            response (ChatResponse): The response to create the content from.
            candidate (MessageDict): The candidate message to create the content from.
            index (int): The index of the candidate message.

        Returns:
            ChatMessageContent: The created chat message content.
        """
        metadata = {
            "citation_metadata": candidate.get("citation_metadata"),
            "filters": response.filters,
            "choice_index": index,
        }
        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            role=int_to_role[int(candidate.get("author"))],  # TODO (moonbox3): why is author coming back as '1'?
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            role=int_to_role[int(candidate.get("author"))],  # TODO (moonbox3): why is author coming back as '1'?
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
            role=int_to_role[int(candidate.get("author"))],  # TODO (moonbox3): why is author coming back as '1'?
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
            role=int_to_role[int(candidate.get("author"))],  # TODO (moonbox3): why is author coming back as '1'?
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
            role=int_to_role[int(candidate.get("author"))],  # TODO (moonbox3): why is author coming back as '1'?
=======
            role=int_to_role[int(candidate.get("author"))],  # TODO: why is author coming back as '1'?
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            content=candidate.get("content"),
        )

    async def get_streaming_chat_message_contents(
        self,
        messages: list[tuple[str, str]],
        settings: GooglePalmPromptExecutionSettings,
        **kwargs: Any,
    ):
        """Return a streaming chat message.

        Raises:
            NotImplementedError: Google Palm API does not currently support streaming
        """
        raise NotImplementedError("Google Palm API does not currently support streaming")

    async def get_text_contents(
        self,
        prompt: str,
        settings: GooglePalmPromptExecutionSettings,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.
=======
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (GooglePalmPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        settings.messages = [{"author": "user", "content": prompt}]
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_chat_request(settings)

        return [self._create_text_content(response, candidate) for candidate in response.candidates]

    def _create_text_content(self, response: ChatResponse, candidate: MessageDict) -> TextContent:
        """Create a text content object from a response.

        Args:
            response (ChatResponse): The response to create the content from.
            candidate (MessageDict): The candidate message to create the content from.

        Returns:
            TextContent: The created text content.
        """
        metadata = {"citation_metadata": candidate.get("citation_metadata"), "filters": response.filters}
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            text=candidate.get("content"),
        )

    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: GooglePalmPromptExecutionSettings,
    ):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
        """Return a streaming text content.

        Raises:
            NotImplementedError: Google Palm API does not currently support streaming
        """
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        raise NotImplementedError("Google Palm API does not currently support streaming")

    async def _send_chat_request(
        self,
        settings: GooglePalmPromptExecutionSettings,
    ) -> Any:
        """Completes the given user message.

        If len(messages) > 1, and a
        conversation has not been initiated yet, it is assumed that chat history
        is needed for context. All messages preceding the last message will be
        utilized for context. This also enables Google PaLM to utilize memory
        and plugins, which should be stored in the messages parameter as system
        messages.

        Args:
            settings (GooglePalmPromptExecutionSettings): The request settings.

        Returns:
            The completion.
        """
        if settings is None:
            raise ValueError("The request settings cannot be `None`")

        if settings.messages[-1]["author"] != "user":
            raise ServiceInvalidRequestError("The last message must be from the user")
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
            raise ServiceResponseException(
                "Google PaLM service failed to complete the prompt",
                ex,
            ) from ex
        return response

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return GooglePalmChatPromptExecutionSettings
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head

    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
    ) -> List[Dict[str, Optional[str]]]:
        """
        Prepare the chat history for a request, allowing customization of the key names for role/author,
        and optionally overriding the role.
        """
        standard_out = super()._prepare_chat_history_for_request(chat_history)
        for message in standard_out:
            message["author"] = message.pop("role")
        return standard_out
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
