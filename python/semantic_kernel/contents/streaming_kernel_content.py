# Copyright (c) Microsoft. All rights reserved.
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class StreamingKernelContent(KernelBaseModel, ABC):
    """Base class for all streaming kernel contents."""

    choice_index: int
    inner_content: Optional[Any] = None
    ai_model_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass

    @abstractmethod
    def __add__(self, other: "StreamingKernelContent") -> "StreamingKernelContent":
        pass
