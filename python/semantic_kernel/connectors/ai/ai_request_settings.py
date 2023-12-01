from typing import Any, Dict

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class AIRequestSettings(SKBaseModel):
    service_id: str = Field(min_length=1)
    extension_data: Dict[str, Any] = Field(default_factory=dict)

    def create_options(self, **kwargs) -> Dict[str, Any]:
        return self.model_dump(exclude={"service_id", "extension_data"})
