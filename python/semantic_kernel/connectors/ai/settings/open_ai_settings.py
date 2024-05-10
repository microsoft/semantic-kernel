# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    """OpenAI model settings

    The settings are first loaded from environment variables with the prefix 'AZURE_OPENAI_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'OPENAI_' are:
    - api_key: SecretStr - OpenAI API key, see https://platform.openai.com/account/api-keys

    Optional settings for prefix 'OPENAI_' are:
    - org_id: str | None - This is usually optional unless your account belongs to multiple organizations.
    - ai_model_id: str | None - The OpenAI model ID to use. If not provided, the default model (gpt-3.5-turbo) is used.
    """

    use_env_settings_file: bool = False
    org_id: str | None = None
    api_key: SecretStr
    ai_model_id: str = "gpt-3.5-turbo"

    model_config = SettingsConfigDict(env_prefix="OPENAI_", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.use_env_settings_file:
            # Update model_config dynamically to include .env file if needed
            self.__config__.model_config = SettingsConfigDict(
                env_prefix="OPENAI_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
            )
