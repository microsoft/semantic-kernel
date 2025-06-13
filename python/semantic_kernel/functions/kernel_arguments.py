# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from semantic_kernel.const import DEFAULT_SERVICE_NAME

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class KernelArguments(dict):
    """The arguments sent to the KernelFunction."""

    def __init__(
        self,
        settings: (
            "PromptExecutionSettings | list[PromptExecutionSettings] | dict[str, PromptExecutionSettings] | None"
        ) = None,
        **kwargs: Any,
    ):
        """Initializes a new instance of the KernelArguments class.

        This is a dict-like class with the additional field for the execution_settings.

        This class is derived from a dict, hence behaves the same way,
        just adds the execution_settings as a dict, with service_id and the settings.

        Args:
            settings (PromptExecutionSettings | List[PromptExecutionSettings] | None):
                The settings for the execution.
                If a list is given, make sure all items in the list have a unique service_id
                as that is used as the key for the dict.
            **kwargs (dict[str, Any]): The arguments for the function invocation, works similar to a regular dict.
        """
        super().__init__(**kwargs)
        settings_dict = None
        if settings:
            settings_dict = {}
            if isinstance(settings, dict):
                settings_dict = settings
            elif isinstance(settings, list):
                settings_dict = {s.service_id or DEFAULT_SERVICE_NAME: s for s in settings}
            else:
                settings_dict = {settings.service_id or DEFAULT_SERVICE_NAME: settings}
        self.execution_settings: dict[str, "PromptExecutionSettings"] | None = settings_dict

    def __bool__(self) -> bool:
        """Returns True if the arguments have any values."""
        has_arguments = self.__len__() > 0
        has_execution_settings = self.execution_settings is not None and len(self.execution_settings) > 0
        return has_arguments or has_execution_settings

    def __or__(self, value: dict) -> "KernelArguments":
        """Merges a KernelArguments with another KernelArguments or dict.

        This implements the `|` operator for KernelArguments.
        """
        if not isinstance(value, dict):
            raise TypeError(
                f"TypeError: unsupported operand type(s) for |: '{type(self).__name__}' and '{type(value).__name__}'"
            )

        # Merge execution settings
        new_execution_settings = (self.execution_settings or {}).copy()
        if isinstance(value, KernelArguments) and value.execution_settings:
            new_execution_settings |= value.execution_settings
        # Create a new KernelArguments with merged dict values
        return KernelArguments(settings=new_execution_settings, **(dict(self) | dict(value)))

    def __ror__(self, value: dict) -> "KernelArguments":
        """Merges a dict with a KernelArguments.

        This implements the right-side `|` operator for KernelArguments.
        """
        if not isinstance(value, dict):
            raise TypeError(
                f"TypeError: unsupported operand type(s) for |: '{type(value).__name__}' and '{type(self).__name__}'"
            )

        # Merge execution settings
        new_execution_settings = {}
        if isinstance(value, KernelArguments) and value.execution_settings:
            new_execution_settings = value.execution_settings.copy()
        if self.execution_settings:
            new_execution_settings |= self.execution_settings

        # Create a new KernelArguments with merged dict values
        return KernelArguments(settings=new_execution_settings, **(dict(value) | dict(self)))
