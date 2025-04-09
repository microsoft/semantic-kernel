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
    - chat_model_id: str - The chat model ID. (Env var OLLAMA_CHAT_MODEL_ID)
    - text_model_id: str - The text model ID. (Env var OLLAMA_TEXT_MODEL_ID)
    - embedding_model_id: str - The embedding model ID. (Env var OLLAMA_EMBEDDING_MODEL_ID)

    Optional settings for prefix 'OLLAMA' are:
    - host: HttpsUrl - The endpoint of the Ollama service. (Env var OLLAMA_HOST)
    """

    env_prefix: ClassVar[str] = "OLLAMA_"

    chat_model_id: str | None = None
    text_model_id: str | None = None
    embedding_model_id: str | None = None
    host: str | None = None
