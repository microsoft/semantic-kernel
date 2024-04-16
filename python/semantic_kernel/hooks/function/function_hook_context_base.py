# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.hooks.kernel_hook_context_base import KernelHookContextBase


class FunctionContext(KernelHookContextBase):
    """Base class for Function Hook Contexts."""

    result: FunctionResult | None = None
    exception: Exception | None = None
