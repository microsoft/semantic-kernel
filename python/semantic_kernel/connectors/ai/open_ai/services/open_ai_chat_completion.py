# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    overload,
)

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_choices, _parse_message

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletion(
    OpenAIConfigBase, ChatCompletionClientBase, OpenAITextCompletionBase
):
    """OpenAI Chat completion class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        log: Optional[Logger] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
            log: The logger instance to use. (Optional)
            is_assistant: Whether this is an assistant. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Logger] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log {Optional[Logger]} -- The logger instance to use. (Optional)
            is_assistant: Whether this is an assistant. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Logger] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log {Optional[Logger]} -- The logger instance to use. (Optional)
            is_assistant: Whether this is an assistant. (Optional)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        is_assistant: Optional[bool] = False,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            log  -- The logger instance to use. (Optional) (Deprecated)
        """
        if log:
            logger.warning(
                "The `log` parameter is deprecated. Please use the `logging` module instead."
            )
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            ai_model_type=OpenAIModelTypes.CHAT,
            default_headers=default_headers,
            async_client=async_client,
            is_assistant=is_assistant,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAIChatCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAIChatCompletion(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            org_id=settings.get("org_id"),
            default_headers=settings.get("default_headers"),
            log=settings.get("log"),
            is_assistant=settings.get("is_assistant", False),
        )

    # --------------------------------- OpenAI Assistants -------------------------

    def get_assistant_id(self) -> Optional[str]:
        """
        Get the assistant id if this is an assistant and has been initialized.

        Returns:
            Optional[str]: The assistant id or None if this is not an assistant or not initialized.
        """
        if self.is_assistant and self.assistant_id is not None:
            return self.assistant_id
        return None

    async def delete_thread_async(self) -> None:
        """
        Delete the current thread if this is an assistant.

        Returns:
            None
        """
        if (
            self.is_assistant
            and self.assistant_id is not None
            and self.thread_id is not None
        ):
            await self.client.beta.threads.delete(self.thread_id)

    async def delete_assistant_async(self) -> None:
        """
        Delete the current assistant if this is an assistant.

        Returns:
            None
        """
        if self.is_assistant and self.assistant_id is not None:
            await self.client.beta.assistants.delete(self.assistant_id)
