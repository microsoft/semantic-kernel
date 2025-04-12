# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class BraveSettings(KernelBaseSettings):
    """Brave Connector settings.

    The settings are first loaded from environment variables with the prefix 'BRAVE_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'BRAVE_' are:
    - api_key: SecretStr - The Brave API key (Env var BRAVE_API_KEY)

    """

    env_prefix: ClassVar[str] = "BRAVE_"

    api_key: SecretStr
