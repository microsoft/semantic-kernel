# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import overload

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import OpenAITextCompletionBase

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletion(OpenAITextCompletionBase, OpenAIConfigBase):
    """OpenAI Text Completion class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        service_id: str | None = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str | None} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            org_id {str | None} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str | None} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str | None} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            org_id {str | None} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {AsyncOpenAI | None} -- An existing client to use. (Optional)
        """
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            service_id=service_id,
            ai_model_type=OpenAIModelTypes.TEXT,
            default_headers=default_headers,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, str]) -> "OpenAITextCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """
        if "default_headers" in settings and isinstance(settings["default_headers"], str):
            settings["default_headers"] = json.loads(settings["default_headers"])
        return OpenAITextCompletion(
            ai_model_id=settings["ai_model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
        )
