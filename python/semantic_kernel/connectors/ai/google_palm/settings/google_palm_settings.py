# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class GooglePalmSettings(BaseSettings):
    """Google Palm model settings.

    The settings are first loaded from environment variables with the prefix 'GOOGLE_PALM_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'GOOGLE_PALM_' are:
    - api_key: SecretStr - GooglePalm API key, see https://developers.generativeai.google/products/palm
        (Env var GOOGLE_PALM_API_KEY)
    - env_file_path: {str | None} - Use the environment settings file as a fallback to environment variables. (Optional)
    - chat_model_id: str | None - The GooglePalm chat model ID to use.
        (Env var GOOGLE_PALM_CHAT_MODEL_ID)
    - text_model_id: str | None - The GooglePalm text model ID to use.
        (Env var GOOGLE_PALM_TEXT_MODEL_ID)
    - embedding_model_id: str | None - The GooglePalm embedding model ID to use.
        (Env var GOOGLE_PALM_EMBEDDING_MODEL_ID)
    """

    env_file_path: str | None = None
    api_key: SecretStr | None = None
    chat_model_id: str | None = None
    text_model_id: str | None = None
    embedding_model_id: str | None = None

    class Config:
        """Pydantic configuration settings."""

        env_prefix = "GOOGLE_PALM_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        """Create the settings object."""
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
