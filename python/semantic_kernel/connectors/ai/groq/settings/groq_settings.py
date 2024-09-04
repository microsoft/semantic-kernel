# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class GroqSettings(KernelBaseSettings):
    """Groq model settings.

    The settings are first loaded from environment variables with the prefix 'GROQ_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'GROQ_' are:
    - api_key: Groq API key, see https://console.groq.com/docs/api-keys
        (Env var GROQ_API_KEY)
    - model_id: The Groq model ID to use, see https://console.groq.com/docs/models.
        (Env var GROQ_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "GROQ_"

    api_key: SecretStr
    org_id: str | None = None
    model: str | None = None
    chat_model_id: str | None = None
