# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings

# Global (US/CA) endpoint
ASTRAFLOW_GLOBAL_BASE_URL = "https://api-us-ca.umodelverse.ai/v1"
# China endpoint
ASTRAFLOW_CN_BASE_URL = "https://api.modelverse.cn/v1"


class AstraflowSettings(KernelBaseSettings):
    """Astraflow model settings.

    Astraflow (by UCloud / 优刻得) is an OpenAI-compatible AI model aggregation
    platform supporting 200+ models.  Sign up at https://astraflow.ucloud.cn/

    The settings are first loaded from environment variables with the prefix
    'ASTRAFLOW_'.  If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.  If the settings are
    not found in the .env file, the settings are ignored; however, validation
    will fail alerting that the settings are missing.

    Optional settings for prefix 'ASTRAFLOW_' are:
    - api_key: Astraflow API key for the global (US/CA) endpoint.
        (Env var ASTRAFLOW_API_KEY)
    - cn_api_key: Astraflow API key for the China endpoint.
        (Env var ASTRAFLOW_CN_API_KEY)
    - base_url: str - The base URL of the Astraflow endpoint.
        Defaults to the global endpoint ``https://api-us-ca.umodelverse.ai/v1``.
        Set to ``https://api.modelverse.cn/v1`` to use the China endpoint.
        (Env var ASTRAFLOW_BASE_URL)
    - chat_model_id: str | None - The Astraflow chat model ID to use.
        (Env var ASTRAFLOW_CHAT_MODEL_ID)
    - embedding_model_id: str | None - The Astraflow embedding model ID to use.
        (Env var ASTRAFLOW_EMBEDDING_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path
    """

    env_prefix: ClassVar[str] = "ASTRAFLOW_"

    api_key: SecretStr | None = None
    cn_api_key: SecretStr | None = None
    base_url: str = ASTRAFLOW_GLOBAL_BASE_URL
    chat_model_id: str | None = None
    embedding_model_id: str | None = None
