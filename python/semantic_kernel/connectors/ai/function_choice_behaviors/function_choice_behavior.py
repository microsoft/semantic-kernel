# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from pydantic.dataclasses import dataclass

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5


@dataclass
class FunctionChoiceConfiguration:
    """Class that holds the configured functions for function calling."""

    functions: list["KernelFunctionMetadata"] | None = None


class FunctionChoiceBehavior(KernelBaseModel):
    """Class that controls function calling behavior.

    Args:
        enable_kernel_functions (bool): Enable kernel functions.
        max_auto_invoke_attempts (int): The maximum number of auto invoke attempts.

    Attributes:
        function_qualified_names (list[str] | None): The short names of the functions to use.
            For example, ["plugin1.function1", "plugin2.function2"]
        enable_kernel_functions (bool): Enable kernel functions.
        max_auto_invoke_attempts (int): The maximum number of auto invoke attempts.

    Properties:
        auto_invoke_kernel_functions: Check if the kernel functions should be auto-invoked.
            Determined as max_auto_invoke_attempts > 0.

    Methods:
        configure: Configures the settings for the function call behavior,
            the default version in this class, does nothing, use subclasses for different behaviors.

    Class methods:
        Auto: Returns KernelFunctions class with auto_invoke enabled, all functions.
        NoInvoke: Returns KernelFunctions class with auto_invoke disabled, all functions.
        EnableFunctions: Set the enable kernel functions flag, filtered functions, auto_invoke optional.
        RequiredFunction: Set the required function flag, auto_invoke optional.

    """

    function_qualified_names: list[str] | None = None
    enable_kernel_functions: bool = True
    max_auto_invoke_attempts: int = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS

    @classmethod
    def from_function_call_behavior(cls, behavior: "FunctionCallBehavior"):
        """Convert FunctionCallBehavior to FunctionChoiceBehavior.
        
        This method is used while FunctionCallBehavior is still supported.

        Args:
            behavior (FunctionCallBehavior): The function call behavior to convert.

        Returns:
            FunctionChoiceBehavior: The converted function choice behavior.
        """
        from semantic_kernel.connectors.ai.function_call_behavior import (
            EnabledFunctions,
            KernelFunctions,
            RequiredFunction,
        )

        if isinstance(behavior, KernelFunctions):
            return cls.Auto()
        if isinstance(behavior, EnabledFunctions):
            return cls.EnableFunctions(filters=behavior.filters)
        if isinstance(behavior, RequiredFunction):
            return cls.RequiredFunction(function_fully_qualified_name=behavior.function_fully_qualified_name)
        return cls(
            enable_kernel_functions=behavior.enable_kernel_functions,
            max_auto_invoke_attempts=behavior.max_auto_invoke_attempts
        )

    @property
    def auto_invoke_kernel_functions(self):
        """Check if the kernel functions should be auto-invoked."""
        return self.max_auto_invoke_attempts > 0

    @auto_invoke_kernel_functions.setter
    def auto_invoke_kernel_functions(self, value: bool):
        """Set the auto_invoke_kernel_functions flag."""
        if not value:
            self.max_auto_invoke_attempts = 0
        else:
            if self.max_auto_invoke_attempts == 0:
                self.max_auto_invoke_attempts = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Configures the settings for the function call behavior.

        Using the base FunctionChoiceBehavior means that you manually have to set tool_choice and tools.

        For different behaviors, use the subclasses of FunctionChoiceBehavior:
            Auto (all functions in the Kernel)
            NoInvoke (all functions in the Kernel, but not invoked)
            EnabledFunctions (filtered set of functions from the Kernel)
            RequiredFunction (a single function)

        By default, the update_settings_callback is called with FunctionCallConfiguration,
        which contains a list of available functions or a list of required functions, it also
        takes the PromptExecutionSettings object.

        It should update the prompt execution settings with the available functions or required functions.

        Alternatively you can override this class and add your own logic in the configure method.
        """
        return

    @classmethod
    def Auto(cls) -> "KernelFunctions":
        """Returns KernelFunctions class with auto_invoke enabled."""
        return KernelFunctions(max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)

    @classmethod
    def NoInvoke(cls) -> "KernelFunctions":
        """Returns KernelFunctions class with auto_invoke disabled.

        Function calls are enabled in this case, just not invoked.
        """
        return KernelFunctions(max_auto_invoke_attempts=0)

    @classmethod
    def EnableFunctions(
        cls,
        auto_invoke: bool = False,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ],
    ) -> "EnableFunctions":
        """Set the enable kernel functions flag."""
        return EnabledFunctions(
            filters=filters, max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if auto_invoke else 0
        )

    @classmethod
    def RequiredFunction(
        cls,
        auto_invoke: bool = False,
        *,
        function_fully_qualified_name: str,
    ) -> "RequiredFunction":
        """Set the required function flag."""
        return RequiredFunction(
            function_fully_qualified_name=function_fully_qualified_name,
            max_auto_invoke_attempts=1 if auto_invoke else 0,
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "FunctionChoiceBehavior":
        """Create a FunctionChoiceBehavior from a dictionary."""
        type_map = {
            "auto": KernelFunctions,
            "no_invoke": KernelFunctions,
            "enable_functions": EnabledFunctions,
            "required": RequiredFunction
        }
        behavior_type = data.pop("type", "auto")
        function_qualified_names = data.pop("functions", [])
        return type_map[behavior_type](function_qualified_names=function_qualified_names, **data)


class KernelFunctions(FunctionChoiceBehavior):
    """Function call behavior for making all kernel functions available for tool calls."""

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Set the options for the tool call behavior in the settings."""
        if self.enable_kernel_functions:
            update_settings_callback(
                FunctionChoiceConfiguration(functions=kernel.get_full_list_of_function_metadata()), settings
            )


class EnabledFunctions(FunctionChoiceBehavior):
    """Function call behavior for making a filtered set of functions available for tool calls."""

    filters: dict[
        Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
    ]

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Set the options for the tool call behavior in the settings."""
        if self.enable_kernel_functions:
            _ = (
                [KernelFunctionMetadata(name.replace('.', '-')) for name in self.function_qualified_names]
                if self.function_qualified_names
                else kernel.get_full_list_of_function_metadata()
            )
            # TODO (evmattso): filter here
            update_settings_callback(
                FunctionChoiceConfiguration(functions=kernel.get_list_of_function_metadata(self.filters)),
                settings,
            )


class RequiredFunction(FunctionChoiceBehavior):
    """Function call behavior for making a single function available for tool calls."""

    function_fully_qualified_name: str

    def configure(
        self,
        kernel: "Kernel",
        update_settings_callback: Callable[..., None],
        settings: "PromptExecutionSettings",
    ) -> None:
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions:
            return
        # since using this always calls this single function, we do not want to allow repeated calls
        if self.max_auto_invoke_attempts > 1:
            self.max_auto_invoke_attempts = 1
        update_settings_callback(
            FunctionChoiceConfiguration(
                functions=kernel.get_list_of_function_metadata(
                    {"included_functions": [self.function_fully_qualified_name]}
                )
            ),
            settings,
        )
