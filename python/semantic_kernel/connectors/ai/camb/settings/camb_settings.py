# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class CambSettings(KernelBaseSettings):
    """Camb.ai settings.

    The settings are first loaded from environment variables with
    the prefix 'CAMB_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'CAMB_' are:
    - api_key: SecretStr - The camb.ai API key. (Env var CAMB_API_KEY)

    Optional settings for prefix 'CAMB_' are:
    - text_to_audio_model_id: str - The TTS model ID. (Env var CAMB_TEXT_TO_AUDIO_MODEL_ID)
    """

    env_prefix: ClassVar[str] = "CAMB_"

    api_key: SecretStr
    text_to_audio_model_id: str | None = None
