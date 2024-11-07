# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from pydantic.dataclasses import dataclass
from typing_extensions import deprecated

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5


@dataclass
class FunctionCallConfiguration:
    """Class that holds the configured functions for function calling."""

    available_functions: list["KernelFunctionMetadata"] | None = None
    required_functions: list["KernelFunctionMetadata"] | None = None


@deprecated("The `FunctionCallBehavior` class is deprecated; use `FunctionChoiceBehavior` instead.", category=None)
class FunctionCallBehavior(KernelBaseModel):
    """Class that controls function calling behavior.

    DEPRECATED: This class has been replaced by FunctionChoiceBehavior.

    Args:
        enable_kernel_functions (bool): Enable kernel functions.
        max_auto_invoke_attempts (int): The maximum number of auto invoke attempts.

    Attributes:
        enable_kernel_functions (bool): Enable kernel functions.
        max_auto_invoke_attempts (int): The maximum number of auto invoke attempts.

    Properties:
        auto_invoke_kernel_functions: Check if the kernel functions should be auto-invoked.
            Determined as max_auto_invoke_attempts > 0.

    Methods:
        configure: Configures the settings for the function call behavior,
            the default version in this class, does nothing, use subclasses for different behaviors.

    Class methods:
        AutoInvokeKernelFunctions: Returns KernelFunctions class with auto_invoke enabled, all functions.
        EnableKernelFunctions: Returns KernelFunctions class with auto_invoke disabled, all functions.
        EnableFunctions: Set the enable kernel functions flag, filtered functions, auto_invoke optional.
        RequiredFunction: Set the required function flag, auto_invoke optional.

    """

    enable_kernel_functions: bool = True
    max_auto_invoke_attempts: int = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS

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

        Using the base ToolCallBehavior means that you manually have to set tool_choice and tools.

        For different behaviors, use the subclasses of ToolCallBehavior:
            KernelFunctions (all functions in the Kernel)
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
    @deprecated("Use the `FunctionChoiceBehavior` `Auto` class instead.")
    def AutoInvokeKernelFunctions(cls) -> "KernelFunctions":
        """Returns KernelFunctions class with auto_invoke enabled."""
        return KernelFunctions(max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)

    @classmethod
    @deprecated("Use the `FunctionChoiceBehavior` `Auto` class method instead.")
    def EnableKernelFunctions(cls) -> "KernelFunctions":
        """Returns KernelFunctions class with auto_invoke disabled.

        Function calls are enabled in this case, just not invoked.
        """
        return KernelFunctions(max_auto_invoke_attempts=0)

    @classmethod
    @deprecated("Use the `FunctionChoiceBehavior` `Auto` class method instead.")
    def EnableFunctions(
        cls,
        auto_invoke: bool = False,
        *,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ]
        | None = {},
    ) -> "EnabledFunctions":
        """Set the enable kernel functions flag."""
        return EnabledFunctions(
            filters=filters, max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS if auto_invoke else 0
        )

    @classmethod
    @deprecated("Use the `FunctionChoiceBehavior` `Required` class method instead.")
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


@deprecated("Use the `FunctionChoiceBehavior` `Auto` class instead.")
class KernelFunctions(FunctionCallBehavior):
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
                FunctionCallConfiguration(available_functions=kernel.get_full_list_of_function_metadata()), settings
            )


@deprecated("Use the `FunctionChoiceBehavior` `Auto` class instead.")
class EnabledFunctions(FunctionCallBehavior):
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
            update_settings_callback(
                FunctionCallConfiguration(available_functions=kernel.get_list_of_function_metadata(self.filters)),
                settings,
            )


@deprecated("Use the `FunctionChoiceBehavior` `Required` class instead.")
class RequiredFunction(FunctionCallBehavior):
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
            FunctionCallConfiguration(
                required_functions=kernel.get_list_of_function_metadata({
                    "included_functions": [self.function_fully_qualified_name]
                })
            ),
            settings,
        )
