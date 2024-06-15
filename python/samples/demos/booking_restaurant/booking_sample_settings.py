# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class BookingSampleSettings(BaseSettings):
    """Restaurant Booking Sample settings

    The settings are first loaded from environment variables with the prefix 'BOOKING_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'BOOKING_' are:
    - client_id = The App Registration Client ID (Env var BOOKING_CLIENT_ID)
    - tenant_id = The App Registration Tenant ID (Env var BOOKING_TENANT_ID)
    - client_secret = The App Registration Client Secret (Env var BOOKING_CLIENT_SECRET)
    - business_id = The sample booking service ID (Env var BOOKING_BUSINESS_ID)
    - service_id = The sample booking service ID (Env var BOOKING_SERVICE_ID)

    For more information on these required settings, please see the sample's README.md file.
    """

    env_file_path: str | None = None
    client_id: str
    tenant_id: str
    client_secret: SecretStr
    business_id: str
    service_id: str

    class Config:
        env_prefix = "BOOKING_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        if kwargs.get("env_file_path"):
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
