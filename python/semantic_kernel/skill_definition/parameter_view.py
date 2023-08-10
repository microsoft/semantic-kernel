# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.validation import validate_function_param_name


class ParameterView(SKBaseModel):
    name: str
    description: str
    default_value: str

    def __init__(self, name: str, description: str, default_value: str) -> None:
        validate_function_param_name(name)
        super().__init__(
            name=name, description=description, default_value=default_value
        )
