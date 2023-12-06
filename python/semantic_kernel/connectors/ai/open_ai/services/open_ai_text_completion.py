# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Dict, Mapping, Optional, overload

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)


class OpenAITextCompletion(OpenAITextCompletionBase, OpenAIConfigBase):
    """OpenAI Text Completion class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
            log: The logger instance to use. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log {Optional[Logger]} -- The logger instance to use. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log {Optional[Logger]} -- The logger instance to use. (Optional)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Logger] = None,
        async_client: Optional[AsyncOpenAI] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log {Optional[Logger]} -- The logger instance to use. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
        """
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            log=log,
            ai_model_type=OpenAIModelTypes.TEXT,
            default_headers=default_headers,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAITextCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAITextCompletion(
            ai_model_id=settings["ai_model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            default_headers=settings.get("default_headers"),
            log=settings.get("log"),
        )
