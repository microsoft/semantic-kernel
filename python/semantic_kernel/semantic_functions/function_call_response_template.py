import json
from dataclasses import dataclass
from typing import Dict


@dataclass
class FunctionCallResponseTemplate:
    name: str
    arguments: str

    @property
    def parsed_arguments(self) -> Dict[str, str]:
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return {}
