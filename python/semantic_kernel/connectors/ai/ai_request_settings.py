from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class AIRequestSettings(SKBaseModel):
    service_id: Optional[str] = Field(None, min_length=1)
    extension_data: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data: Dict[str, Any]):
        super().__init__(**data)
        for key, value in self.extension_data.items():
            if key in self.keys:
                setattr(self, key, value)

    def prepare_settings_dict(self, **kwargs) -> Dict[str, Any]:
        return self.model_dump(
            exclude={"service_id", "extension_data"},
            exclude_none=True,
            by_alias=True,
        )

    @property
    def keys(self):
        """Get the keys of the request settings."""
        return self.model_fields.keys()

    def update_from_completion_config(self, config: "AIRequestSettings") -> None:
        """Update the request settings from a completion config."""
        self.service_id = config.service_id
        self.extension_data.update(config.extension_data)

    @classmethod
    def from_completion_config(cls, config: "AIRequestSettings") -> "AIRequestSettings":
        """Create a request settings from a completion config."""
        return cls(
            service_id=config.service_id,
            extension_data=config.extension_data,
        )
