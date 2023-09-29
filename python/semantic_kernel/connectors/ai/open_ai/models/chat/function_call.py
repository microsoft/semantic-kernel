"""Class to hold chat messages."""
import json
from typing import Dict, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.sk_pydantic import SKBaseModel


class FunctionCall(SKBaseModel):
    """Class to hold a function call response."""

    name: str
    arguments: str

    def parse_arguments(self) -> Dict[str, str]:
        """Parse the arguments into a dictionary."""
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return None

    def to_context_variables(self) -> ContextVariables:
        """Return the arguments as a ContextVariables instance."""
        args = self.parse_arguments()
        return ContextVariables(variables={k.lower(): v for k, v in args.items()})

    def split_name(self) -> Tuple[str, str]:
        """Split the name into a skill and function name."""
        if "-" not in self.name:
            return None, self.name
        return self.name.split("-")

    def split_name_dict(self) -> dict:
        """Split the name into a skill and function name."""
        parts = self.split_name()
        return {"skill_name": parts[0], "function_name": parts[1]}
