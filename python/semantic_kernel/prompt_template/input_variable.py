# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputVariable(KernelBaseModel):
    name: str = Field(..., alias="name")
    description: Optional[str] = Field("", alias="description")
    default: Optional[Any] = Field("", alias="default")
    is_required: Optional[bool] = Field(True, alias="is_required")
    json_schema: Optional[str] = Field("", alias="json_schema")
