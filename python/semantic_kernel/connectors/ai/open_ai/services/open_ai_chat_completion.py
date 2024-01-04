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
        log: Optional[Any] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
            log: The logger instance to use. (Optional) (Deprecated)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
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
            log  -- The logger instance to use. (Optional) (Deprecated)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
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
            log  -- The logger instance to use. (Optional) (Deprecated)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        log: Optional[Any] = None,
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
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAIChatCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAIChatCompletion(
            ai_model_id=settings["ai_model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            default_headers=settings.get("default_headers"),
        )

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> Union[
        Tuple[Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[FunctionCall]]],
    ]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = False
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        if len(response.choices) == 1:
            return _parse_message(response.choices[0].message)
        else:
            return [_parse_message(choice.message) for choice in response.choices]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = True
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        # parse the completion text(s) and yield them
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in chunk.choices:
                    text, index = _parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = _parse_choices(chunk.choices[0])
                yield text

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAIChatRequestSettings
