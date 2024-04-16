# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import FUNCTION_PARAM_NAME_REGEX


class KernelParameterMetadata(KernelBaseModel):
    name: str = Field(..., pattern=FUNCTION_PARAM_NAME_REGEX)
    description: str = ""
    default_value: Any = None
    type_: str | None = Field(default="str", alias="type")
    is_required: bool | None = False
    type_object: Any = None
