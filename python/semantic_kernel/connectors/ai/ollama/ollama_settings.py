# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class OllamaSettings(KernelBaseSettings):
    """Ollama settings.

    The settings are first loaded from environment variables with
    the prefix 'OLLAMA_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'OLLAMA' are:
    - model: str - Model name. (Env var OLLAMA_MODEL)

    Optional settings for prefix 'OLLAMA' are:
    - host: HttpsUrl - The endpoint of the Ollama service. (Env var OLLAMA_HOST)
    """

    env_prefix: ClassVar[str] = "OLLAMA_"

    model: str
    host: str | None = None
