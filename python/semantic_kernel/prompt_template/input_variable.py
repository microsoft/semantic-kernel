# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Optional

from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputVariable(KernelBaseModel):
    name: str
    description: Optional[str] = ""
    default: Optional[Any] = ""
    is_required: Optional[bool] = True
    json_schema: Optional[str] = ""
