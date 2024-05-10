# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BookingSampleSettings(BaseSettings):
    """Restaurant Booking Sample settings

    The settings are first loaded from environment variables with the prefix 'BOOKING_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'BOOKING_' are:
    - client_id = The App Registration Client ID
    - tenant_id = The App Registration Tenant ID
    - client_secret = The App Registration Client Secret
    - business_id = The sample booking service ID
    - service_id = The sample booking service ID

    For more information on these required settings, please see the sample's README.md file.
    """

    use_env_settings_file: bool = False
    client_id: str
    tenant_id: str
    client_secret: SecretStr
    business_id: str
    service_id: str

    model_config = SettingsConfigDict(env_prefix="BOOKING_", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.use_env_settings_file:
            # Update model_config dynamically to include .env file if needed
            self.__config__.model_config = SettingsConfigDict(
                env_prefix="BOOKING_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
            )
