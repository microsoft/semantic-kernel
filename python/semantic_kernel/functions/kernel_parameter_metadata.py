# Copyright (c) Microsoft. All rights reserved.


from typing import Any, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import FUNCTION_PARAM_NAME_REGEX


class KernelParameterMetadata(KernelBaseModel):
    name: str = Field(..., pattern=FUNCTION_PARAM_NAME_REGEX)
    description: str = ""
    default_value: Any = None
    type_: Optional[str] = Field(default="str", alias="type")
    is_required: Optional[bool] = False
    type_object: Any = None
