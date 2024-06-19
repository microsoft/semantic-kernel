# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic.dataclasses import dataclass

from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5

logger = logging.getLogger(__name__)


class FunctionChoiceType(Enum):
    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


def _check_missing_functions(function_names: list[str], kernel_function_metadata: set) -> None:
    try:
        qualified_names = {metadata.fully_qualified_name for metadata in kernel_function_metadata}
        missing_functions = [name for name in function_names if name not in qualified_names]
    except Exception:
        logger.exception("Error checking for missing functions.")
        return

    if missing_functions:
        raise ServiceInvalidExecutionSettingsError(
            f"Unable to find the required function(s) `{', '.join(missing_functions)}` "
            f"in the list of available kernel functions: {', '.join(qualified_names)}."
        )


@dataclass
class FunctionCallChoiceConfiguration:
    available_functions: list["KernelFunctionMetadata"] | None = None
    required_functions: list["KernelFunctionMetadata"] | None = None


class FunctionChoiceBehavior(KernelBaseModel):
    config_function_qualified_names: list[str] | None = None
    enable_kernel_functions: bool = True
    maximum_auto_invoke_attempts: int = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS
    filters: (
        dict[Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]]
        | None
    ) = None
    function_fully_qualified_names: list[str] | None = None
    type: FunctionChoiceType | None = None

    @classmethod
    def from_function_call_behavior(cls, behavior: "FunctionCallBehavior") -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior from a FunctionCallBehavior."""
        from semantic_kernel.connectors.ai.function_call_behavior import (
            EnabledFunctions,
            KernelFunctions,
            RequiredFunction,
        )

        if isinstance(behavior, KernelFunctions):
            return cls.Auto()
        if isinstance(behavior, (EnabledFunctions, RequiredFunction)):
            return cls.Required(
                auto_invoke=behavior.auto_invoke_kernel_functions,
                filters=behavior.filters,
                function_fully_qualified_names=behavior.function_fully_qualified_names,
            )
        return cls(
            enable_kernel_functions=behavior.enable_kernel_functions,
            max_auto_invoke_attempts=behavior.max_auto_invoke_attempts,
        )

    @property
    def auto_invoke_kernel_functions(self):
        """Whether to auto-invoke kernel functions."""
        return self.maximum_auto_invoke_attempts > 0

    @auto_invoke_kernel_functions.setter
    def auto_invoke_kernel_functions(self, value: bool):
        self.maximum_auto_invoke_attempts = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if value else 0

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Configure the function choice behavior."""
        full_kernel_function_metadata = set(kernel.get_full_list_of_function_metadata())

        config = None
        if self.config_function_qualified_names:
            valid_fqns = [name.replace(".", "-") for name in self.config_function_qualified_names]
            _check_missing_functions(valid_fqns, full_kernel_function_metadata)
            config = FunctionCallChoiceConfiguration(
                required_functions=kernel.get_list_of_function_metadata({"included_functions": valid_fqns})
            )
        elif self.type == FunctionChoiceType.AUTO:
            config = FunctionCallChoiceConfiguration(available_functions=kernel.get_full_list_of_function_metadata())
        elif self.type == FunctionChoiceType.REQUIRED:
            if self.function_fully_qualified_names:
                valid_fqns = [name.replace(".", "-") for name in self.config_function_qualified_names]
                _check_missing_functions(valid_fqns, full_kernel_function_metadata)
                config = FunctionCallChoiceConfiguration(
                    required_functions=kernel.get_list_of_function_metadata({"included_functions": valid_fqns})
                )
            elif self.filters:
                config = FunctionCallChoiceConfiguration(
                    available_functions=kernel.get_list_of_function_metadata(self.filters)
                )

        if config:
            update_settings_callback(config, settings, self.type)
        else:
            logger.warning("No functions were configured for the required functions behavior.")

    @classmethod
    def Auto(cls) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior with all available plugins/functions from the kernel."""
        return cls(type=FunctionChoiceType.AUTO, max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)

    @classmethod
    def NoneInvoke(cls) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior with no auto-invocation of functions."""
        return cls(type=FunctionChoiceType.NONE, max_auto_invoke_attempts=0)

    @classmethod
    def Required(
        cls,
        auto_invoke: bool = False,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        function_fully_qualified_names: list[str] | None = None,
    ) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior with required functions."""
        return cls(
            type=FunctionChoiceType.REQUIRED,
            filters=filters,
            function_fully_qualified_names=function_fully_qualified_names,
            max_auto_invoke_attempts=1 if auto_invoke else 0,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior from a dictionary."""
        type_map = {
            "auto": FunctionChoiceType.AUTO,
            "none": FunctionChoiceType.NONE,
            "required": FunctionChoiceType.REQUIRED,
        }
        behavior_type = data.pop("type", "auto")
        function_qualified_names = data.pop("functions", [])
        return cls(type=type_map[behavior_type], config_function_qualified_names=function_qualified_names, **data)
