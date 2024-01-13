from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class StreamingKernelContent(SKBaseModel, ABC):
    inner_content: Any
    ai_model_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Post init method for model."""
        self.create_metadata_dictionary()

    @abstractmethod
    def to_string(self) -> str:
        pass

    @abstractmethod
    def to_byte_array(self) -> bytes:
        pass

    def create_metadata_dictionary(self) -> None:
        """Create metadata dictionary."""
        pass
