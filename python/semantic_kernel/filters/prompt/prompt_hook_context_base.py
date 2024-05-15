# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING

from semantic_kernel.filters.kernel_filter_context_base import KernelFilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


class PromptHookContextBase(KernelFilterContextBase):
    """Base class for Prompt Hook Contexts."""

    kernel: "Kernel"
