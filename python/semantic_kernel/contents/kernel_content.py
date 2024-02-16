# Copyright (c) Microsoft. All rights reserved.
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelContent(KernelBaseModel, ABC):
    """Base class for all kernel contents."""

    inner_content: Optional[Any] = None
    ai_model_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        pass
