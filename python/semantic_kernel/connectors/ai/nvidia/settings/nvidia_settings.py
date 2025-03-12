# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class NvidiaSettings(KernelBaseSettings):
    """Nvidia model settings.

    The settings are first loaded from environment variables with the prefix 'NVIDIA_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'NVIDIA_' are:
    - api_key: NVIDIA API key, see https://console.NVIDIA.com/settings/keys
        (Env var NVIDIA_API_KEY)
    - base_url: HttpsUrl | None - base_url: The url of the NVIDIA endpoint. The base_url consists of the endpoint,
                and more information refer https://docs.api.nvidia.com/nim/reference/
                use endpoint if you only want to supply the endpoint.
                (Env var NVIDIA_BASE_URL)
    - embedding_model_id: str | None - The NVIDIA embedding model ID to use, for example, nvidia/nv-embed-v1.
        (Env var NVIDIA_EMBEDDING_MODEL_ID)
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "NVIDIA_"

    api_key: SecretStr
    base_url: str = "https://integrate.api.nvidia.com/v1"
    embedding_model_id: str | None
