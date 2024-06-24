# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic.dataclasses import dataclass

from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class, experimental_function

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5

logger = logging.getLogger(__name__)


@experimental_class
class FunctionChoiceType(Enum):
    """The type of function choice behavior."""

    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


@experimental_function
def _check_for_missing_functions(function_names: list[str], kernel_function_metadata: set) -> None:
    """Check for missing functions in the kernel function metadata."""
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


@experimental_class
@dataclass
class FunctionCallChoiceConfiguration:
    available_functions: list["KernelFunctionMetadata"] | None = None


@experimental_class
class FunctionChoiceBehavior(KernelBaseModel):
    """Class that controls function choice behavior.

    Attributes:
        enable_kernel_functions: Enable kernel functions.
        max_auto_invoke_attempts: The maximum number of auto invoke attempts.
        filters: Filters for the function choice behavior.
        function_fully_qualified_names: The fully qualified names of the functions.
        type: The type of function choice behavior.

    Properties:
        auto_invoke_kernel_functions: Check if the kernel functions should be auto-invoked.
            Determined as max_auto_invoke_attempts > 0.

    Methods:
        configure: Configures the settings for the function call behavior,
            the default version in this class, does nothing, use subclasses for different behaviors.

    Class methods:
        Auto: Returns FunctionChoiceAuto class with auto_invoke enabled, and the desired functions
            based on either the specified filters or the full qualified names.
        NoneInvoke: Returns FunctionChoiceNone class with auto_invoke disabled, and the desired functions
            based on either the specified filters or the full qualified names.
        Required: Returns FunctionChoiceRequired class with auto_invoke enabled, and the desired functions
            based on either the specified filters or the full qualified names.
    """

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

        if isinstance(behavior, (EnabledFunctions, KernelFunctions)):
            return cls.Auto(
                auto_invoke=behavior.auto_invoke_kernel_functions,
                filters=behavior.filters if hasattr(behavior, "filters") else None,
            )
        if isinstance(behavior, (RequiredFunction)):
            return cls.Required(
                auto_invoke=behavior.auto_invoke_kernel_functions,
                function_fully_qualified_names=[behavior.function_fully_qualified_name]
                if hasattr(behavior, "function_fully_qualified_name")
                else None,
            )
        return cls(
            enable_kernel_functions=behavior.enable_kernel_functions,
            maximum_auto_invoke_attempts=behavior.max_auto_invoke_attempts,
        )

    @property
    def auto_invoke_kernel_functions(self):
        """Return True if auto_invoke_kernel_functions is enabled."""
        return self.maximum_auto_invoke_attempts > 0

    @auto_invoke_kernel_functions.setter
    def auto_invoke_kernel_functions(self, value: bool):
        """Set the auto_invoke_kernel_functions property."""
        self.maximum_auto_invoke_attempts = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if value else 0

    def _check_and_get_config(
        self, kernel: "Kernel", fully_qualified_names: list[str] | None = None, filters: dict[str, Any] | None = {}
    ) -> FunctionCallChoiceConfiguration:
        """Check for missing functions and get the function call choice configuration."""
        full_kernel_function_metadata = set(kernel.get_full_list_of_function_metadata())

        if fully_qualified_names:
            _check_for_missing_functions(fully_qualified_names, full_kernel_function_metadata)
            return FunctionCallChoiceConfiguration(
                available_functions=kernel.get_list_of_function_metadata({"included_functions": fully_qualified_names})
            )
        if filters:
            return FunctionCallChoiceConfiguration(available_functions=kernel.get_list_of_function_metadata(filters))
        return FunctionCallChoiceConfiguration(available_functions=kernel.get_full_list_of_function_metadata())

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Configure the function choice behavior."""
        if not self.enable_kernel_functions:
            return

        config = self.get_config(kernel)

        if config:
            update_settings_callback(config, settings, self.type)

    def get_config(self, kernel: "Kernel") -> FunctionCallChoiceConfiguration:
        """Get the function call choice configuration based on the type."""
        return self._check_and_get_config(kernel, self.function_fully_qualified_names, self.filters)

    @classmethod
    def Auto(
        cls,
        auto_invoke: bool = True,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        function_fully_qualified_names: list[str] | None = None,
        **kwargs,
    ) -> "FunctionChoiceBehavior":
        """Creates a FunctionChoiceBehavior with type AUTO."""
        kwargs.setdefault("maximum_auto_invoke_attempts", DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if auto_invoke else 0)
        return cls(
            type=FunctionChoiceType.AUTO,
            filters=filters,
            function_fully_qualified_names=function_fully_qualified_names,
            **kwargs,
        )

    @classmethod
    def NoneInvoke(
        cls,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        function_fully_qualified_names: list[str] | None = None,
        **kwargs,
    ) -> "FunctionChoiceBehavior":
        """Creates a FunctionChoiceBehavior with type NONE."""
        kwargs.setdefault("maximum_auto_invoke_attempts", 0)
        return cls(
            type=FunctionChoiceType.NONE,
            filters=filters,
            function_fully_qualified_names=function_fully_qualified_names,
            **kwargs,
        )

    @classmethod
    def Required(
        cls,
        auto_invoke: bool = True,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        function_fully_qualified_names: list[str] | None = None,
        **kwargs,
    ) -> "FunctionChoiceBehavior":
        """Creates a FunctionChoiceBehavior with type REQUIRED."""
        kwargs.setdefault("maximum_auto_invoke_attempts", 1 if auto_invoke else 0)
        return cls(
            type=FunctionChoiceType.REQUIRED,
            filters=filters,
            function_fully_qualified_names=function_fully_qualified_names,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior from a dictionary."""
        type_map = {
            "auto": cls.Auto,
            "none": cls.NoneInvoke,
            "required": cls.Required,
        }
        behavior_type = data.pop("type", "auto")
        auto_invoke = data.pop("auto_invoke", False)
        filters = data.pop("filters", None)
        function_qualified_names = data.pop("functions", [])

        return type_map[behavior_type](
            auto_invoke=auto_invoke,
            filters=filters,
            function_fully_qualified_names=function_qualified_names,
            **data,
        )
