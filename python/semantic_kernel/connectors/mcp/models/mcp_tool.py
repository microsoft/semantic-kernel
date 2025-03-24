# Copyright (c) Microsoft. All rights reserved.
from typing import ClassVar

from mcp.types import Tool

from semantic_kernel.connectors.mcp.models.mcp_tool_parameters import MCPToolParameters
from semantic_kernel.exceptions import ServiceInvalidTypeError
from semantic_kernel.kernel_pydantic import KernelBaseModel


class MCPTool(KernelBaseModel):
    """Semantic Kernel Class for MCP Tool."""

    parameters: ClassVar[list[MCPToolParameters]] = []

    @classmethod
    def from_mcp_tool(cls, tool: Tool):
        """Creates an MCPFunction instance from a tool."""
        properties: dict = tool.inputSchema.get("properties")
        required: dict = tool.inputSchema.get("required")
        # Check if 'properties' is missing or not a dictionary
        if properties is None or not isinstance(properties, dict):
            raise ServiceInvalidTypeError("""Could not parse tool properties,
                please ensure your server returns properties as a dictionary and required as a array.""")
        parameters = [
            MCPToolParameters(
                name=prop_name,
                required=prop_name in required,
                **prop_details,
            )
            for prop_name, prop_details in properties.items()
        ]

        return cls(parameters=parameters)
