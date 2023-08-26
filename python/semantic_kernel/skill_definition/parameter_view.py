# Copyright (c) Microsoft. All rights reserved.
from typing import Dict

from pydantic import Field, validator

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.validation import validate_function_param_name


class ParameterView(SKBaseModel):
    name: str
    description: str
    default_value: str
    type_: str = Field(default="string", alias="type")
    required: bool = True

    @validator("name")
    def validate_name(cls, name: str):
        validate_function_param_name(name)
        return name

    @property
    def callable_function_object(self) -> Dict[str, str]:
        """Return the parameter, ready for a function call setup."""
        return {"description": self.description, "type": self.type_}
