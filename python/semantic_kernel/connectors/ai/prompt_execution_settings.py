from typing import Any, Dict, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class PromptExecutionSettings(KernelBaseModel):
    """Base class for prompt execution settings.

    Can be used by itself or as a base class for other prompt execution settings. The methods are used to create
    specific prompt execution settings objects based on the keys in the extension_data field, this way you can
    create a generic PromptExecutionSettings object in your application, which get's mapped into the keys of the
    prompt execution settings that each services returns by using the service.get_prompt_execution_settings() method.

    Parameters:
        service_id (str): The service ID to use for the request.
        extension_data (Dict[str, Any], optional): Any additional data to send with the request. Defaults to None.
        kwargs (Any): Additional keyword arguments,
            these are attempted to parse into the keys of the specific prompt execution settings.
    Methods:
        prepare_settings_dict: Prepares the settings as a dictionary for sending to the AI service.
        update_from_prompt_execution_settings: Update the keys from another prompt execution settings object.
        from_prompt_execution_settings: Create a prompt execution settings from another prompt execution settings object.
    """  # noqa: E501

    service_id: Optional[str] = Field(None, min_length=1)
    extension_data: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, service_id: Optional[str] = None, **kwargs: Any):
        extension_data = kwargs.pop("extension_data", {})
        extension_data.update(kwargs)
        super().__init__(service_id=service_id, extension_data=extension_data)
        self.unpack_extension_data()

    @property
    def keys(self):
        """Get the keys of the prompt execution settings."""
        return self.model_fields.keys()

    def prepare_settings_dict(self, **kwargs) -> Dict[str, Any]:
        return self.model_dump(
            exclude={
                "service_id",
                "extension_data",
            },
            exclude_none=True,
            by_alias=True,
        )

    def update_from_prompt_execution_settings(self, config: "PromptExecutionSettings") -> None:
        """Update the prompt execution settings from a completion config."""
        if config.service_id is not None:
            self.service_id = config.service_id
        config.pack_extension_data()
        self.extension_data.update(config.extension_data)
        self.unpack_extension_data()

    @classmethod
    def from_prompt_execution_settings(cls, config: "PromptExecutionSettings") -> "PromptExecutionSettings":
        """Create a prompt execution settings from a completion config."""
        config.pack_extension_data()
        return cls(
            service_id=config.service_id,
            extension_data=config.extension_data,
        )

    def unpack_extension_data(self) -> None:
        """Update the prompt execution settings from extension data.

        Does not overwrite existing values with None.
        """
        for key, value in self.extension_data.items():
            if value is None:
                continue
            if key in self.keys:
                setattr(self, key, value)

    def pack_extension_data(self) -> None:
        """Update the extension data from the prompt execution settings."""
        for key in self.model_fields_set:
            if key not in ["service_id", "extension_data"] and getattr(self, key) is not None:
                self.extension_data[key] = getattr(self, key)
