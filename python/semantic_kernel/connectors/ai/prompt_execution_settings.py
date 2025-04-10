# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Any, TypeVar

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="PromptExecutionSettings")


class PromptExecutionSettings(KernelBaseModel):
    """Base class for prompt execution settings.

    Can be used by itself or as a base class for other prompt execution settings. The methods are used to create
    specific prompt execution settings objects based on the keys in the extension_data field, this way you can
    create a generic PromptExecutionSettings object in your application, which gets mapped into the keys of the
    prompt execution settings that each services returns by using the service.get_prompt_execution_settings() method.

    Attributes:
        service_id (str | None): The service ID to use for the request.
        extension_data (Dict[str, Any]): Any additional data to send with the request.
        function_choice_behavior (FunctionChoiceBehavior | None): The function choice behavior settings.

    Methods:
        prepare_settings_dict: Prepares the settings as a dictionary for sending to the AI service.
        update_from_prompt_execution_settings: Update the keys from another prompt execution settings object.
        from_prompt_execution_settings: Create a prompt execution settings from another prompt execution settings.
    """

    service_id: Annotated[str | None, Field(min_length=1)] = None
    extension_data: dict[str, Any] = Field(default_factory=dict)
    function_choice_behavior: Annotated[FunctionChoiceBehavior | None, Field(exclude=True)] = None

    @model_validator(mode="before")
    @classmethod
    def parse_function_choice_behavior(cls: type[_T], data: Any) -> dict[str, Any]:
        """Parse the function choice behavior data."""
        if isinstance(data, dict):
            function_choice_behavior_data = data.get("function_choice_behavior")
            if function_choice_behavior_data:
                if isinstance(function_choice_behavior_data, str):
                    data["function_choice_behavior"] = FunctionChoiceBehavior.from_string(function_choice_behavior_data)
                elif isinstance(function_choice_behavior_data, dict):
                    data["function_choice_behavior"] = FunctionChoiceBehavior.from_dict(function_choice_behavior_data)
        return data

    def __init__(self, service_id: str | None = None, **kwargs: Any):
        """Initialize the prompt execution settings.

        Args:
            service_id (str): The service ID to use for the request.
            kwargs (Any): Additional keyword arguments,
                these are attempted to parse into the keys of the specific prompt execution settings.
        """
        extension_data = kwargs.pop("extension_data", {})
        function_choice_behavior = kwargs.pop("function_choice_behavior", None)
        extension_data.update(kwargs)
        super().__init__(
            service_id=service_id, extension_data=extension_data, function_choice_behavior=function_choice_behavior
        )
        self.unpack_extension_data()

    @property
    def keys(self):
        """Get the keys of the prompt execution settings."""
        return self.__class__.model_fields.keys()

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings as a dictionary for sending to the AI service.

        By default, this method excludes the service_id and extension_data fields.
        As well as any fields that are None.
        """
        return self.model_dump(
            exclude={
                "service_id",
                "extension_data",
                "structured_json_response",
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
    def from_prompt_execution_settings(cls: type[_T], config: "PromptExecutionSettings") -> _T:
        """Create a prompt execution settings from a completion config."""
        config.pack_extension_data()
        return cls(
            service_id=config.service_id,
            extension_data=config.extension_data,
            function_choice_behavior=config.function_choice_behavior,
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
