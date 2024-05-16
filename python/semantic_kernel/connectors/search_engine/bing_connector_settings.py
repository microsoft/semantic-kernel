# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class BingSettings(BaseSettings):
    """Bing Connector settings

    The settings are first loaded from environment variables with the prefix 'BING_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'BING_' are:
    - api_key: SecretStr - The Bing API key (Env var BING_API_KEY)

    """

    env_file_path: str | None = None
    api_key: SecretStr | None = None

    class Config:
        env_prefix = "BING_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
