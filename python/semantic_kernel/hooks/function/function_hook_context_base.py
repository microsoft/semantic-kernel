# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from pydantic import Field

from semantic_kernel.hooks.kernel_hook_context_base import KernelHookContextBase


class FunctionHookContextBase(KernelHookContextBase):
    """Base class for Function Hook Contexts."""

    is_cancel_requested: bool = Field(default=False, init_var=False)
    cancel_reason: str = Field(default="", init_var=False)

    def cancel(self, cancel_reason: str | None = None):
        if not cancel_reason:
            cancel_reason = f"Function execution was canceled, by {getattr(self, '__name__', 'unknown')}"
        self.cancel_reason = cancel_reason
        self.is_cancel_requested = True
