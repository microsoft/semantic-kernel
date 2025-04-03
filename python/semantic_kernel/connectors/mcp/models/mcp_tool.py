# Copyright (c) Microsoft. All rights reserved.
from mcp.types import Tool
from pydantic import Field

from semantic_kernel.connectors.mcp.models.mcp_tool_parameters import MCPToolParameters
from semantic_kernel.exceptions import ServiceInvalidTypeError
from semantic_kernel.kernel_pydantic import KernelBaseModel


class MCPTool(KernelBaseModel):
    """Semantic Kernel Class for MCP Tool."""

    parameters: list[MCPToolParameters] = Field(default_factory=list)

    @classmethod
    def from_mcp_tool(cls, tool: Tool):
        """Creates an MCPFunction instance from a tool."""
        properties = tool.inputSchema.get("properties", None)
        required = tool.inputSchema.get("required", None)
        # Check if 'properties' is missing or not a dictionary
        if properties is None or not isinstance(properties, dict):
            raise ServiceInvalidTypeError("""Could not parse tool properties,
            please ensure your server returns properties as a dictionary and required as an array.""")
        if required is None or not isinstance(required, list):
            raise ServiceInvalidTypeError("""Could not parse tool required fields,
            please ensure your server returns required as an array.""")
        parameters = [
            MCPToolParameters(
                name=prop_name,
                required=prop_name in required,
                **prop_details,
            )
            for prop_name, prop_details in properties.items()
        ]

        return cls(parameters=parameters)
