# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar, Literal

from pydantic import SecretStr, model_validator

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class MiniMaxSettings(KernelBaseSettings):
    """MiniMax model settings.

    The settings are first loaded from environment variables with the prefix 'MINIMAX_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'MINIMAX_' are:
    - api_key: SecretStr - MiniMax API key, see https://platform.minimax.io/docs
        (Env var MINIMAX_API_KEY)
    - region: Literal["global_en", "cn_zh"] - The MiniMax region to target. The global endpoint
        is used by default; select "cn_zh" to use the China region endpoint.
        (Env var MINIMAX_REGION)
    - base_url: str | None - The MiniMax OpenAI-compatible endpoint. When not provided it is
        resolved from the selected region.
        (Env var MINIMAX_BASE_URL)
    - chat_model_id: str | None - The MiniMax chat model ID to use, for example, MiniMax-M3.
        (Env var MINIMAX_CHAT_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    # Regional OpenAI-compatible endpoints documented at
    # https://platform.minimax.io/docs/api-reference/api-overview
    REGIONAL_BASE_URLS: ClassVar[dict[str, str]] = {
        "global_en": "https://api.minimax.io/v1",
        "cn_zh": "https://api.minimaxi.com/v1",
    }

    env_prefix: ClassVar[str] = "MINIMAX_"

    api_key: SecretStr | None = None
    region: Literal["global_en", "cn_zh"] = "global_en"
    base_url: str | None = None
    chat_model_id: str | None = None

    @model_validator(mode="after")
    def _resolve_base_url(self) -> "MiniMaxSettings":
        """Resolve the base URL from the selected region when it is not explicitly provided."""
        if self.base_url is None:
            self.base_url = self.REGIONAL_BASE_URLS[self.region]
        return self
