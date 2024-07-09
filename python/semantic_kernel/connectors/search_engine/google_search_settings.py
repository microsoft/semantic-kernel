# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class GoogleSearchSettings(KernelBaseSettings):
    """Google Search Connector settings.

    The settings are first loaded from environment variables with the prefix 'GOOGLE_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Required settings for prefix 'GOOGLE_' are:
    - search_api_key: SecretStr - The Google Search API key (Env var GOOGLE_API_KEY)

    Optional settings for prefix 'GOOGLE_' are:
    - search_engine_id: str - The Google search engine ID (Env var GOOGLE_SEARCH_ENGINE_ID)
    - env_file_path: str | None - if provided, the .env settings are read from this file path location
    - env_file_encoding: str - if provided, the .env file encoding used. Defaults to "utf-8".
    """

    env_prefix: ClassVar[str] = "GOOGLE_"

    search_api_key: SecretStr
    search_engine_id: str | None = None
