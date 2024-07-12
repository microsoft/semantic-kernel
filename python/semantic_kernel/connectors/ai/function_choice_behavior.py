# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Literal, TypeVar

from typing_extensions import deprecated

from semantic_kernel.connectors.ai.function_calling_utils import _combine_filter_dicts
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel


DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5

logger = logging.getLogger(__name__)


_T = TypeVar("_T", bound="FunctionChoiceBehavior")


@experimental_class
class FunctionChoiceType(Enum):
    """The type of function choice behavior."""

    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


@experimental_class
class FunctionChoiceBehavior(KernelBaseModel):
    """Class that controls function choice behavior.

    Attributes:
        enable_kernel_functions: Enable kernel functions.
        max_auto_invoke_attempts: The maximum number of auto invoke attempts.
        filters: Filters for the function choice behavior. Available options are: excluded_plugins,
            included_plugins, excluded_functions, or included_functions.
        type_: The type of function choice behavior.

    Properties:
        auto_invoke_kernel_functions: Check if the kernel functions should be auto-invoked.
            Determined as max_auto_invoke_attempts > 0.

    Methods:
        configure: Configures the settings for the function call behavior,
            the default version in this class, does nothing, use subclasses for different behaviors.

    Class methods:
        Auto: Returns FunctionChoiceBehavior class with auto_invoke enabled, and the desired functions
            based on either the specified filters or the full qualified names. The model will decide which function
            to use, if any.
        NoneInvoke: Returns FunctionChoiceBehavior class with auto_invoke disabled, and the desired functions
            based on either the specified filters or the full qualified names. The model does not invoke any functions,
            but can rather describe how it would invoke a function to complete a given task/query.
        Required: Returns FunctionChoiceBehavior class with auto_invoke enabled, and the desired functions
            based on either the specified filters or the full qualified names. The model is required to use one of the
            provided functions to complete a given task/query.
    """

    enable_kernel_functions: bool = True
    maximum_auto_invoke_attempts: int = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS
    filters: (
        dict[Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]]
        | None
    ) = None
    type_: FunctionChoiceType | None = None

    @classmethod
    @deprecated("The `FunctionCallBehavior` class is deprecated; use `FunctionChoiceBehavior` instead.")
    def from_function_call_behavior(cls: type[_T], behavior: "FunctionCallBehavior") -> _T:
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
                filters={"included_functions": [behavior.function_fully_qualified_name]},
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
        self,
        kernel: "Kernel",
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = {},
    ) -> "FunctionCallChoiceConfiguration":
        """Check for missing functions and get the function call choice configuration."""
        from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration

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
            update_settings_callback(config, settings, self.type_)

    def get_config(self, kernel: "Kernel") -> "FunctionCallChoiceConfiguration":
        """Get the function call choice configuration based on the type."""
        return self._check_and_get_config(kernel, self.filters)

    @classmethod
    def Auto(
        cls: type[_T],
        auto_invoke: bool = True,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        **kwargs,
    ) -> _T:
        """Creates a FunctionChoiceBehavior with type AUTO.

        Returns FunctionChoiceBehavior class with auto_invoke enabled, and the desired functions
        based on either the specified filters or the full qualified names. The model will decide which function
        to use, if any.
        """
        kwargs.setdefault("maximum_auto_invoke_attempts", DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if auto_invoke else 0)
        return cls(
            type_=FunctionChoiceType.AUTO,
            filters=filters,
            **kwargs,
        )

    @classmethod
    def NoneInvoke(
        cls: type[_T],
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        **kwargs,
    ) -> _T:
        """Creates a FunctionChoiceBehavior with type NONE.

        Returns FunctionChoiceBehavior class with auto_invoke disabled, and the desired functions
        based on either the specified filters or the full qualified names. The model does not invoke any functions,
        but can rather describe how it would invoke a function to complete a given task/query.
        """
        kwargs.setdefault("maximum_auto_invoke_attempts", 0)
        return cls(
            type_=FunctionChoiceType.NONE,
            filters=filters,
            **kwargs,
        )

    @classmethod
    def Required(
        cls: type[_T],
        auto_invoke: bool = True,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = None,
        **kwargs,
    ) -> _T:
        """Creates a FunctionChoiceBehavior with type REQUIRED.

        Returns FunctionChoiceBehavior class with auto_invoke enabled, and the desired functions
        based on either the specified filters or the full qualified names. The model is required to use one of the
        provided functions to complete a given task/query.
        """
        kwargs.setdefault("maximum_auto_invoke_attempts", 1 if auto_invoke else 0)
        return cls(
            type_=FunctionChoiceType.REQUIRED,
            filters=filters,
            **kwargs,
        )

    @classmethod
    def from_dict(cls: type[_T], data: dict) -> _T:
        """Create a FunctionChoiceBehavior from a dictionary."""
        type_map = {
            "auto": cls.Auto,
            "none": cls.NoneInvoke,
            "required": cls.Required,
        }
        behavior_type = data.pop("type", "auto")
        auto_invoke = data.pop("auto_invoke", False)
        functions = data.pop("functions", None)
        filters = data.pop("filters", None)

        if functions:
            valid_fqns = [name.replace(".", "-") for name in functions]
            if filters:
                filters = _combine_filter_dicts(filters, {"included_functions": valid_fqns})
            else:
                filters = {"included_functions": valid_fqns}

        return type_map[behavior_type](  # type: ignore
            auto_invoke=auto_invoke,
            filters=filters,
            **data,
        )

    @classmethod
    def from_string(cls: type[_T], data: str) -> _T:
        """Create a FunctionChoiceBehavior from a string.

        This method converts the provided string to a FunctionChoiceBehavior object
        for the specified type.
        """
        type_value = data.lower()
        if type_value == "auto":
            return cls.Auto()
        if type_value == "none":
            return cls.NoneInvoke()
        if type_value == "required":
            return cls.Required()
        raise ServiceInitializationError(
            f"The specified type `{type_value}` is not supported. Allowed types are: `auto`, `none`, `required`."
        )
