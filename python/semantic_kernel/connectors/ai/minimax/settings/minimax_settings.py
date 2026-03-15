# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class MiniMaxSettings(KernelBaseSettings):
    """MiniMax model settings.

    The settings are first loaded from environment variables with the prefix 'MINIMAX_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'MINIMAX_' are:
    - api_key: MiniMax API key
        (Env var MINIMAX_API_KEY)
    - base_url: str - The url of the MiniMax API endpoint. Defaults to https://api.minimax.io/v1.
        (Env var MINIMAX_BASE_URL)
    - chat_model_id: str | None - The MiniMax chat model ID to use, for example, MiniMax-M2.5.
        (Env var MINIMAX_CHAT_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "MINIMAX_"

    api_key: SecretStr | None = None
    base_url: str = "https://api.minimax.io/v1"
    chat_model_id: str | None = None
