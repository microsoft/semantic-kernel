"""Class to hold chat messages."""
import json
from typing import Any, Dict, List, Optional

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel


class FunctionCall(KernelBaseModel):
    """Class to hold a function call response."""

    name: Optional[str] = None
    arguments: Optional[str] = None
    # TODO: check if needed
    id: Optional[str] = None

    def __add__(self, other: Optional["FunctionCall"]) -> "FunctionCall":
        """Add two function calls together, combines the arguments, ignores the name."""
        if not other:
            return self
        return FunctionCall(
            name=self.name or other.name,
            arguments=(self.arguments or "") + (other.arguments or ""),
            id=self.id or other.id,
        )

    def parse_arguments(self) -> Optional[Dict[str, Any]]:
        """Parse the arguments into a dictionary."""
        if not self.arguments:
            return None
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return None

    def to_kernel_arguments(self) -> KernelArguments:
        """Return the arguments as a KernelArguments instance."""
        args = self.parse_arguments()
        if not args:
            return KernelArguments()
        return KernelArguments(**args)

    def split_name(self) -> List[str]:
        """Split the name into a plugin and function name."""
        if not self.name:
            raise ValueError("Name is not set.")
        if "-" not in self.name:
            return ["", self.name]
        return self.name.split("-", maxsplit=1)

    def split_name_dict(self) -> dict:
        """Split the name into a plugin and function name."""
        parts = self.split_name()
        return {"plugin_name": parts[0], "function_name": parts[1]}
