# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Mapping

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletion(OpenAITextCompletionBase, OpenAIConfigBase):
    """OpenAI Text Completion class."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str | None} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id {str | None} -- Service ID tied to the execution settings.
            api_key {str | None} -- The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id {str | None} -- The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            env_file_path {str | None} -- Use the environment settings file as a fallback to
                environment variables. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(env_file_path=env_file_path)
        except ValidationError as e:
            logger.warning(f"Failed to load OpenAI pydantic settings: {e}")

        api_key = api_key or (
            openai_settings.api_key.get_secret_value() if openai_settings and openai_settings.api_key else None
        )
        org_id = org_id or (openai_settings.org_id if openai_settings and openai_settings.org_id else None)
        ai_model_id = ai_model_id or (
            openai_settings.text_model_id if openai_settings and openai_settings.text_model_id else None
        )

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
            ai_model_id=settings.get("ai_model_id", None),
            api_key=settings.get("api_key", None),
            org_id=settings.get("org_id", None),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path", None),
        )
