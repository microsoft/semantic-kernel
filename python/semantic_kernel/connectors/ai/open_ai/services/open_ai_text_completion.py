# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Dict, Mapping, Optional

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
from semantic_kernel.connectors.ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletion(OpenAITextCompletionBase, OpenAIConfigBase):
    """OpenAI Text Completion class."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        use_env_settings_file: bool = False,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str | None} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            use_env_settings_file {bool} -- Use the environment settings file as a fallback to
                environment variables. (Optional)
        """
        try:
            openai_settings = OpenAISettings(use_env_settings_file=use_env_settings_file)
        except ValidationError as e:
            logger.error(f"Error loading OpenAI settings: {e}")
            raise ServiceInitializationError("Error loading OpenAI settings") from e
        api_key = openai_settings.api_key.get_secret_value()
        org_id = openai_settings.org_id
        model_id = ai_model_id or openai_settings.ai_model_id

        super().__init__(
            ai_model_id=model_id,
            api_key=api_key,
            org_id=org_id,
            service_id=service_id,
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
        if "default_headers" in settings and isinstance(settings["default_headers"], str):
            settings["default_headers"] = json.loads(settings["default_headers"])
        return OpenAITextCompletion(
            ai_model_id=settings["ai_model_id"],
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            use_env_settings_file=settings.get("use_env_settings_file", False),
        )
