# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING

from semantic_kernel.hooks.kernel_hook_context_base import KernelHookContextBase

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


class PromptHookContextBase(KernelHookContextBase):
    """Base class for Prompt Hook Contexts."""

    kernel: "Kernel"
