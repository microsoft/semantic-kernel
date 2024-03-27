# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelContent(KernelBaseModel, ABC):
    """Base class for all kernel contents."""

    inner_content: Any = None
    ai_model_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        """Get the string representation of the content."""
        pass
