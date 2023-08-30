"""Class to hold chat messages."""
import json
from typing import Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.sk_pydantic import SKBaseModel


class FunctionCall(SKBaseModel):
    """Class to hold a function call."""
    name: str
    arguments: str

    def to_context_variables(self) -> ContextVariables:
        """Return the arguments as a ContextVariables instance."""
        try:
            args = json.loads(self.arguments)
        except json.JSONDecodeError:
            return None
        return ContextVariables(variables=args)

    def split_name(self) -> Tuple[str, str]:
        """Split the name into a skill and function name."""
        return self.name.split("-")
