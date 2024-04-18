# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5


class ToolCallBehavior(KernelBaseModel):
    """
    This, at its start, is a very slim class. The reason that this class is necessary
    is because during auto invoking function calls for OpenAI streaming chat completions,
    we need a way to toggle a boolean to kick us out of the async generator/loop that is started
    related to the max auto invoke attempts. Booleans are immutable therefore if its state is
    changed inside a method, we're creating a new boolean, which is not what we want. By wrapping
    this flag inside of a class, when we do change its state, it is reflected outside of the method.
    """

    enable_kernel_functions: bool = True
    max_auto_invoke_attempts: int = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS
    max_use_attempts: int | None = None
    allow_any_requested_kernel_function: bool = False

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

    def configure_options(self, kernel: "Kernel", execution_settings: "PromptExecutionSettings"):
        """Set the options for the tool call behavior in the settings.

        Using the base ToolCallBehavior means that you manually have to set tool_choice and tools.

        For different behaviors, use the subclasses of ToolCallBehavior:
            KernelFunctions (all functions in the Kernel)
            EnabledFunctions (filtered set of functions from the Kernel)
            RequiredFunction (a single function)

        """
        return

    @classmethod
    def AutoInvokeKernelFunctions(cls) -> "ToolCallBehavior":
        """Returns KernelFunctions class with auto_invoke enabled."""
        return KernelFunctions(max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)

    @classmethod
    def EnableKernelFunctions(cls) -> "ToolCallBehavior":
        """Returns KernelFunctions class with auto_invoke disabled.

        Tool calls are enabled in this case, just not invoked.
        """
        return KernelFunctions(max_auto_invoke_attempts=0)

    @classmethod
    def EnableFunctions(
        cls,
        auto_invoke: bool = False,
        *,
        filters: dict[Literal["exclude_plugin", "include_plugin", "exclude_function", "include_function"], list[str]],
    ) -> "ToolCallBehavior":
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
    ) -> "ToolCallBehavior":
        """Set the required function flag."""
        return RequiredFunction(
            function_fully_qualified_name=function_fully_qualified_name,
            max_auto_invoke_attempts=1 if auto_invoke else 0,
        )


class KernelFunctions(ToolCallBehavior):
    """Tool call behavior for making all kernel functions available for tool calls."""

    def configure_options(self, kernel: "Kernel", execution_settings: "PromptExecutionSettings"):
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return
        if not hasattr(execution_settings, "tools") and not hasattr(execution_settings, "tool_choice"):
            raise ValueError("The execution settings must have tools and tool_choice attributes.")
        execution_settings.tools = kernel.get_json_schema_of_functions()
        execution_settings.tool_choice = "auto"
        self.allow_any_requested_kernel_function = True


class EnabledFunctions(ToolCallBehavior):
    """Tool call behavior for making a filtered set of functions available for tool calls."""

    filters: dict[Literal["exclude_plugin", "include_plugin", "exclude_function", "include_function"], list[str]]

    def configure_options(self, kernel: "Kernel", execution_settings: "PromptExecutionSettings"):
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return
        if not hasattr(execution_settings, "tools") and not hasattr(execution_settings, "tool_choice"):
            raise ValueError("The execution settings must have tools and tool_choice attributes.")
        execution_settings.tools = kernel.get_json_schema_of_functions(filters=self.filters)
        execution_settings.tool_choice = "auto"
        self.allow_any_requested_kernel_function = True


class RequiredFunction(ToolCallBehavior):
    """Tool call behavior for making a single function available for tool calls."""

    function_fully_qualified_name: str

    def configure_options(self, kernel: "Kernel", execution_settings: PromptExecutionSettings):
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return
        if not hasattr(execution_settings, "tools") and not hasattr(execution_settings, "tool_choice"):
            raise ValueError("The execution settings must have tools and tool_choice attributes.")

        execution_settings.tool_choice = self.function_fully_qualified_name
        execution_settings.tools = kernel.get_json_schema_of_functions(
            filters={"include_function": [self.function_fully_qualified_name]}
        )
        # since using this always calls this single function, we do not want to allow repeated calls
        self.max_auto_invoke_attempts = 1
        self.allow_any_requested_kernel_function = True
