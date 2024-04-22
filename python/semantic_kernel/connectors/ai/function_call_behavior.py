# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5


class FunctionCallBehavior(KernelBaseModel):
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

    def configure(self, kernel: "Kernel") -> tuple[str | None, list[dict[str, Any]] | None]:
        """Set the options for the tool call behavior in the settings.

        Using the base ToolCallBehavior means that you manually have to set tool_choice and tools.

        For different behaviors, use the subclasses of ToolCallBehavior:
            KernelFunctions (all functions in the Kernel)
            EnabledFunctions (filtered set of functions from the Kernel)
            RequiredFunction (a single function)

        Returns:
            tuple[str | None, dict[str, Any] | None]: The tool choice and tools.
        """
        return None, None

    @classmethod
    def AutoInvokeKernelFunctions(cls) -> "FunctionCallBehavior":
        """Returns KernelFunctions class with auto_invoke enabled."""
        return KernelFunctions(max_auto_invoke_attempts=DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)

    @classmethod
    def EnableKernelFunctions(cls) -> "FunctionCallBehavior":
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
    ) -> "FunctionCallBehavior":
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
    ) -> "FunctionCallBehavior":
        """Set the required function flag."""
        return RequiredFunction(
            function_fully_qualified_name=function_fully_qualified_name,
            max_auto_invoke_attempts=1 if auto_invoke else 0,
        )


class KernelFunctions(FunctionCallBehavior):
    """Tool call behavior for making all kernel functions available for tool calls."""

    def configure(self, kernel: "Kernel") -> tuple[str | None, list[dict[str, Any]] | None]:
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return
        return "auto", kernel.get_json_schema_of_functions()


class EnabledFunctions(FunctionCallBehavior):
    """Tool call behavior for making a filtered set of functions available for tool calls."""

    filters: dict[Literal["exclude_plugin", "include_plugin", "exclude_function", "include_function"], list[str]]

    def configure(self, kernel: "Kernel") -> tuple[str | None, list[dict[str, Any]] | None]:
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return
        return "auto", kernel.get_json_schema_of_functions(filters=self.filters)


class RequiredFunction(FunctionCallBehavior):
    """Tool call behavior for making a single function available for tool calls."""

    function_fully_qualified_name: str

    def configure(self, kernel: "Kernel") -> tuple[str | None, list[dict[str, Any]] | None]:
        """Set the options for the tool call behavior in the settings."""
        if not self.enable_kernel_functions and not self.auto_invoke_kernel_functions:
            return None, None
        # since using this always calls this single function, we do not want to allow repeated calls
        if self.max_auto_invoke_attempts > 1:
            self.max_auto_invoke_attempts = 1

        return self.function_fully_qualified_name, kernel.get_json_schema_of_functions(
            filters={"include_function": [self.function_fully_qualified_name]}
        )
