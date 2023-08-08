# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.parameter_view import ParameterView
from semantic_kernel.utils.validation import validate_function_name


class FunctionView(SKBaseModel):
    name: str
    skill_name: str
    description: str
    is_semantic: bool
    parameters: List[ParameterView]
    is_function_call: bool = False
    is_asynchronous: bool = True

    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        parameters: List[ParameterView],
        is_semantic: bool,
        is_function_call: bool = False,
        is_asynchronous: bool = True,
    ) -> None:
        validate_function_name(name)
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
            parameters=parameters,
            is_semantic=is_semantic,
            is_function_call=is_function_call,
            is_asynchronous=is_asynchronous,
        )

    @property
    def function_call_repr(self) -> Dict[str, Any]:
        return {
            "name": f"{self.skill_name}-{self.name}",
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: param.function_call_repr for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required],
            },
        }
