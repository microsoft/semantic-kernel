from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class StreamingKernelContent(SKBaseModel, ABC):
    inner_content: Any
    ai_model_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass
