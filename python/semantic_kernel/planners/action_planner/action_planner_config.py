# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class ActionPlannerConfig(KernelBaseModel):
    excluded_plugins: list[str] = Field(default_factory=list)
    excluded_functions: list[str] = Field(default_factory=list)
    max_tokens: int = 1024
