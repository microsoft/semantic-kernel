# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class AnthropicSettings(KernelBaseSettings):
    """Anthropic model settings.

    The settings are first loaded from environment variables with the prefix 'ANTHROPIC_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'ANTHROPIC_' are:
    - api_key: ANTHROPIC API key, see https://console.anthropic.com/settings/keys
        (Env var ANTHROPIC_API_KEY)
    - chat_model_id: The Anthropic chat model ID to use see https://docs.anthropic.com/en/docs/about-claude/models.
        (Env var ANTHROPIC_CHAT_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "ANTHROPIC_"

    api_key: SecretStr
    chat_model_id: str | None = None
