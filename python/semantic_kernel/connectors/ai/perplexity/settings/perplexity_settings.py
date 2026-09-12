# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class PerplexitySettings(KernelBaseSettings):
    """Perplexity model settings.

    The settings are first loaded from environment variables with the prefix 'PERPLEXITY_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'PERPLEXITY_' are:
    - api_key: SecretStr - Perplexity API key, see https://docs.perplexity.ai/guides/getting-started
        (Env var PERPLEXITY_API_KEY)
    - chat_model_id: str - The Perplexity chat model ID to use. Defaults to 'sonar-pro'.
        See https://docs.perplexity.ai/api-reference/chat-completions-post.
        (Env var PERPLEXITY_CHAT_MODEL_ID)
    - base_url: str - The base URL for the Perplexity API. Defaults to 'https://api.perplexity.ai'.
        (Env var PERPLEXITY_BASE_URL)
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "PERPLEXITY_"

    api_key: SecretStr | None = None
    chat_model_id: str = "sonar-pro"
    base_url: str = "https://api.perplexity.ai"
