# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Coroutine

if TYPE_CHECKING:
    from semantic_kernel.hooks.function_invoked_context import FunctionInvokedContext
    from semantic_kernel.hooks.function_invoking_context import FunctionInvokingContext


class KernelHook:
    """Kernel Hook class."""

    def on_function_invoking(
        self, context: "FunctionInvokingContext"
    ) -> "FunctionInvokingContext | None" | Coroutine[Any, Any, "FunctionInvokingContext | None"]:
        """Called before a function is invoked. This can be made asynchronous."""
        return

    def on_function_invoked(
        self, context: "FunctionInvokedContext"
    ) -> "FunctionInvokedContext | None" | Coroutine[Any, Any, "FunctionInvokingContext | None"]:
        """Called after a function is invoked. This can be made asynchronous."""
        return

    def on_register(self) -> None:
        """Called when the kernel is registered."""
        pass

    def on_exit(self) -> None:
        """Called before the kernel exits."""
        pass
