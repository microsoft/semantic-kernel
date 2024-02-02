# Copyright (c) Microsoft. All rights reserved.


from typing import Any, Optional

from pydantic import Field, field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import validate_function_param_name


class KernelParameterMetadata(KernelBaseModel):
    name: str
    description: str
    default_value: Any
    type_: Optional[str] = Field(default="str", alias="type")
    required: Optional[bool] = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str):
        validate_function_param_name(name)
        return name
