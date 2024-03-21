# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.hooks.function_invoked_context import FunctionInvokedContext
    from semantic_kernel.hooks.function_invoking_context import FunctionInvokingContext


class KernelHook:
    """Kernel Hook class."""

    async def on_function_invoking_async(self, context: "FunctionInvokingContext") -> "FunctionInvokingContext" | None:
        """Called before a function is invoked."""
        return

    async def on_function_invoked_async(self, context: "FunctionInvokedContext") -> "FunctionInvokedContext" | None:
        """Called after a function is invoked."""
        return

    def on_function_invoking(self, context: "FunctionInvokingContext") -> "FunctionInvokingContext" | None:
        """Called before a function is invoked."""
        return

    def on_function_invoked(self, context: "FunctionInvokedContext") -> "FunctionInvokedContext" | None:
        """Called after a function is invoked."""
        return

    def on_register(self):
        """Called when the kernel is registered."""
        pass

    def on_exit(self):
        """Called before the kernel exits."""
        pass
