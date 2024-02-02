# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Dict, Literal, Optional, Tuple

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.orchestration.context_variables import ContextVariables


class ToolCall(KernelBaseModel):
    """Class to hold a tool call response."""

    id: Optional[str] = None
    type: Optional[Literal["function"]] = "function"
    function: Optional[FunctionCall] = None

    def __add__(self, other: Optional["ToolCall"]) -> "ToolCall":
        """Add two tool calls together, combines the function calls, ignores the id."""
        if not other:
            return self
        return ToolCall(
            id=self.id or other.id,
            type=self.type or other.type,
            function=self.function + other.function if self.function else other.function,
        )

    def parse_arguments(self) -> Dict[str, str]:
        """Parse the arguments into a dictionary."""
        try:
            return json.loads(self.function.arguments)
        except json.JSONDecodeError:
            return None

    def to_context_variables(self) -> ContextVariables:
        """Return the arguments as a ContextVariables instance."""
        args = self.parse_arguments()
        return ContextVariables(variables={k.lower(): str(v) for k, v in args.items()})

    def split_name(self) -> Tuple[str, str]:
        """Split the name into a plugin and function name."""
        if "-" not in self.function.name:
            return None, self.function.name
        return self.function.name.split("-")

    def split_name_dict(self) -> dict:
        """Split the name into a plugin and function name."""
        parts = self.split_name()
        return {"plugin_name": parts[0], "function_name": parts[1]}
