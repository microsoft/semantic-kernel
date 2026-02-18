# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

MODELSLAB_CHAT_BASE_URL = "https://modelslab.com/api/uncensored-chat/v1"
MODELSLAB_API_BASE_URL = "https://modelslab.com/api/v6"

# Default models available via ModelsLab uncensored chat
MODELSLAB_DEFAULT_CHAT_MODEL = "llama-3.1-8b-uncensored"
MODELSLAB_CHAT_MODELS: list[str] = [
    "llama-3.1-8b-uncensored",
    "llama-3.1-70b-uncensored",
]


class ModelsLabSettings(BaseSettings):
    """Settings for the ModelsLab connector.

    The settings are first loaded from environment variables with the prefix
    ``MODELSLAB_``. If they are not found, the optional .env file is loaded
    and the settings are loaded from there.

    Required:
    - api_key: ModelsLab API key (``MODELSLAB_API_KEY``)

    Optional:
    - chat_model_id: Model ID to use for chat completion
      (``MODELSLAB_CHAT_MODEL_ID``, default: "llama-3.1-8b-uncensored")
    - chat_base_url: Base URL for the ModelsLab chat API
      (``MODELSLAB_CHAT_BASE_URL``)
    """

    env_prefix: ClassVar[str] = "MODELSLAB_"

    api_key: SecretStr | None = None
    chat_model_id: str | None = None
    chat_base_url: str | None = None

    class Config:
        env_prefix = "MODELSLAB_"
        env_file = None
        extra = "ignore"
