# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class KernelArguments(dict):
    def __init__(
        self,
        settings: Union["PromptExecutionSettings", list["PromptExecutionSettings"]] | None = None,
        **kwargs: Any,
    ):
        """Initializes a new instance of the KernelArguments class,
        this is a dict-like class with the additional field for the execution_settings.

        This class is derived from a dict, hence behaves the same way,
        just adds the execution_settings as a dict, with service_id and the settings.

        Arguments:
            settings {PromptExecutionSettings | list[PromptExecutionSettings] | None} --
                The settings for the execution.
                If a list is given, make sure all items in the list have a unique service_id
                as that is used as the key for the dict.
            **kwargs {dict[str, Any]} -- The arguments for the function invocation, works similar to a regular dict.
        """
        super().__init__(**kwargs)
        settings_dict = {}
        if settings:
            if isinstance(settings, list):
                settings_dict = {s.service_id: s for s in settings}
            else:
                settings_dict = {settings.service_id: settings}
        self.execution_settings: dict[str, "PromptExecutionSettings"] | None = settings_dict
