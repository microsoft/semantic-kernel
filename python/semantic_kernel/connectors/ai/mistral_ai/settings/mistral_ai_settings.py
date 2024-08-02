# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class MistralAISettings(KernelBaseSettings):
    """MistralAI model settings.

    The settings are first loaded from environment variables with the prefix 'MISTRALAI_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'MISTRALAI_' are:
    - api_key: SecretStr - MISTRAL API key, see https://console.mistral.ai/api-keys
        (Env var MISTRALAI_API_KEY)
    - chat_model_id: str | None - The The Mistral AI chat model ID to use see https://docs.mistral.ai/getting-started/models/.
        (Env var MISTRALAI_CHAT_MODEL_ID)
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "MISTRALAI_"

    api_key: SecretStr
    chat_model_id: str | None = None
