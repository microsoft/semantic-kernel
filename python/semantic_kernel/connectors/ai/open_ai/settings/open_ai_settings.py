# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class OpenAISettings(KernelBaseSettings):
    """OpenAI model settings.

    The settings are first loaded from environment variables with the prefix 'OPENAI_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'OPENAI_' are:
    - api_key: SecretStr - OpenAI API key, see https://platform.openai.com/account/api-keys
        (Env var OPENAI_API_KEY)
    - org_id: str | None - This is usually optional unless your account belongs to multiple organizations.
        (Env var OPENAI_ORG_ID)
    - chat_model_id: str | None - The OpenAI chat model ID to use, for example, gpt-3.5-turbo or gpt-4.
        (Env var OPENAI_CHAT_MODEL_ID)
    - text_model_id: str | None - The OpenAI text model ID to use, for example, gpt-3.5-turbo-instruct.
        (Env var OPENAI_TEXT_MODEL_ID)
    - embedding_model_id: str | None - The OpenAI embedding model ID to use, for example, text-embedding-ada-002.
        (Env var OPENAI_EMBEDDING_MODEL_ID)
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "OPENAI_"

    api_key: SecretStr
    org_id: str | None = None
    chat_model_id: str | None = None
    text_model_id: str | None = None
    embedding_model_id: str | None = None
