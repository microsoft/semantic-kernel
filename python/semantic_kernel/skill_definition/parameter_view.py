# Copyright (c) Microsoft. All rights reserved.
from typing import Dict

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.validation import validate_function_param_name


class ParameterView(SKBaseModel):
    name: str
    description: str
    default_value: str
    type: str = "string"
    required: bool = False

    def __init__(self, name: str, description: str, default_value: str) -> None:
        validate_function_param_name(name)
        super().__init__(
            name=name, description=description, default_value=default_value
        )

    @property
    def function_call_dict(self) -> Dict[str, str]:
        """Return the parameter, ready for a function call setup."""
        return {"description": self.description, "type": self.type}
