# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class MiniMaxSettings(KernelBaseSettings):
    """MiniMax credentials and text-to-audio defaults.

    The ``MINIMAX_`` environment prefix is used for API clients. Set
    ``MINIMAX_API_KEY`` and optionally ``MINIMAX_TEXT_TO_AUDIO_MODEL_ID``.
    """

    env_prefix: ClassVar[str] = "MINIMAX_"

    api_key: SecretStr
    text_to_audio_model_id: str | None = None
    text_to_audio_base_url: str = "https://api.minimax.io/v1/t2a_v2"
