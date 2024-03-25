# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputVariable(KernelBaseModel):
    name: str
    description: str | None = ""
    default: Any | None = ""
    is_required: bool | None = True
    json_schema: str | None = ""
