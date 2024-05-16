# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


class PromptHookContextBase(FilterContextBase):
    """Base class for Prompt Hook Contexts."""

    kernel: "Kernel"
