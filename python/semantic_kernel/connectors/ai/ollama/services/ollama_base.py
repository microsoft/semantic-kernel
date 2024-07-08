# Copyright (c) Microsoft. All rights reserved.


from abc import ABC

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OllamaBase(KernelBaseModel, ABC):
    """Ollama service base.

    Args:
        host (Optional[str]): URL of the Ollama server, defaults to None and
            will use the default Ollama service address: http://127.0.0.1:11434
    """

    host: str | None = None
