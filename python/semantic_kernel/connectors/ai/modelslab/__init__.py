# Copyright (c) Microsoft. All rights reserved.

"""ModelsLab connector for Semantic Kernel.

Exposes ModelsLab's OpenAI-compatible chat API through Semantic Kernel's
standard ``ChatCompletionClientBase`` interface.

Quick import
------------
.. code-block:: python

    from semantic_kernel.connectors.ai.modelslab import ModelsLabChatCompletion
"""

from semantic_kernel.connectors.ai.modelslab.modelslab_chat_completion import (
    ModelsLabChatCompletion,
)
from semantic_kernel.connectors.ai.modelslab.modelslab_settings import (
    MODELSLAB_CHAT_BASE_URL,
    MODELSLAB_CHAT_MODELS,
    MODELSLAB_DEFAULT_CHAT_MODEL,
    ModelsLabSettings,
)

__all__ = [
    "ModelsLabChatCompletion",
    "ModelsLabSettings",
    "MODELSLAB_CHAT_BASE_URL",
    "MODELSLAB_CHAT_MODELS",
    "MODELSLAB_DEFAULT_CHAT_MODEL",
]
