import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FunctionCallTemplate:
    name: str
    arguments: str

    @property
    def parsed_arguments(self) -> Dict[str, str]:
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return {}


@dataclass
class FunctionCallParametersPropertiesTemplate:
    name: str
    type: str
    description: str
    required: bool = False

    @property
    def function_call_dict(self):
        return {"description": self.description, "type": self.type}


@dataclass
class FunctionCallDefinitionTemplate:
    name: str
    description: str
    parameters: List[FunctionCallParametersPropertiesTemplate] = field(
        default_factory=list
    )

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
                "required": self.required,
            },
        }

    @property
    def required(self) -> List[str]:
        return [p.name for p in self.parameters if p.required]
