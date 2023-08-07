from dataclasses import dataclass, field
from typing import List

from semantic_kernel.skill_definition.parameter_view import ParameterView


@dataclass
class FunctionCallDefinitionTemplate:
    name: str
    description: str
    parameters: List[ParameterView] = field(default_factory=list)

    @property
    def function_call_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: param.function_call_dict for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required],
            },
        }
