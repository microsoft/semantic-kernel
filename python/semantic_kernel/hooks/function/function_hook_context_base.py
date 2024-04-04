# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from pydantic import Field

from semantic_kernel.hooks.kernel_hook_context_base import KernelHookContextBase


class FunctionHookContextBase(KernelHookContextBase):
    """Base class for Function Hook Contexts."""

    is_cancel_requested: bool = Field(default=False, init_var=False)

    def cancel(self):
        self.is_cancel_requested = True
