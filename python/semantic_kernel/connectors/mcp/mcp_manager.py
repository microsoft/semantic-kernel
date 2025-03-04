# Copyright (c) Microsoft. All rights reserved.
from mcp.types import Tool

from semantic_kernel.connectors.mcp.mcp_server_settings import (
    MCPServerSettings,
)
from semantic_kernel.functions import KernelFunction, KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


async def create_function_from_mcp_server(settings: MCPServerSettings):
    """Loads Function from an MCP Server to KernelFunctions."""
    await settings.initialize_session()
    return await _create_function_from_mcp_server(settings)


async def _create_function_from_mcp_server(settings: MCPServerSettings) -> list[KernelFunction]:
    """Loads Function from an MCP Server to KernelFunctions."""
    # List available tools
    response = await settings.session.list_tools()
    return [_generate_kernel_function_from_tool(tool, settings) for tool in response.tools]


def _generate_kernel_function_from_tool(tool: Tool, settings: MCPServerSettings) -> KernelFunction:
    """Generate a KernelFunction from a tool."""

    @kernel_function(name=tool.name, description=tool.description)
    async def mcp_tool_call(**kwargs):
        return await settings.session.call_tool(tool.name, arguments=kwargs)

    schema = tool.inputSchema
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    parameters: list[KernelParameterMetadata] = [
        KernelParameterMetadata(
            name=prop_name,
            type_=prop_details.get("type", "object"),
            is_required=prop_name in required,
            default_value="",
            schema_data=(
                prop_details.get("items")
                if prop_details.get("items") is not None and isinstance(prop_details.get("items"), dict)
                else {"type": f"{prop_details.get('type')}"}
                if prop_details.get("type")
                else None
            ),
        )
        for prop_name, prop_details in properties.items()
    ]

    return KernelFunctionFromMethod(
        method=mcp_tool_call,
        parameters=parameters,
    )
