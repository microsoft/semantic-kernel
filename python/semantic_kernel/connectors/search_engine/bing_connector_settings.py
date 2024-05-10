# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BingSettings(BaseSettings):
    """Bing Connector settings

    The settings are first loaded from environment variables with the prefix 'BING_'. If the environment variables
    are not found, and the `use_env_settings_file` flag is true, the settings are loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'BING_' are:
    - api_key: SecretStr - The Bing API key

    """
    use_env_settings_file: bool = False
    api_key: SecretStr

    model_config = SettingsConfigDict(env_prefix='BING_', env_file_encoding='utf-8', extra='ignore')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.use_env_settings_file:
            # Update model_config dynamically to include .env file if needed
            self.__config__.model_config = SettingsConfigDict(
                env_prefix='BING_',
                env_file='.env',
                env_file_encoding='utf-8',
                extra='ignore'
            )
