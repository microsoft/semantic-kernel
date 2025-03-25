# Copyright (c) Microsoft. All rights reserved.
from mcp.types import ListToolsResult, Tool

from semantic_kernel.connectors.mcp import (
    MCPTool,
    MCPToolParameters,
)
from semantic_kernel.connectors.mcp.mcp_server_execution_settings import (
    MCPServerExecutionSettings,
)
from semantic_kernel.functions import KernelFunction, KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
async def create_function_from_mcp_server(settings: MCPServerExecutionSettings):
    """Loads Function from an MCP Server to KernelFunctions."""
    async with settings.get_session() as session:
        tools: ListToolsResult = await session.list_tools()
        return _create_kernel_function_from_mcp_server_tools(tools, settings)


def _create_kernel_function_from_mcp_server_tools(
    tools: ListToolsResult, settings: MCPServerExecutionSettings
) -> list[KernelFunction]:
    """Loads Function from an MCP Server to KernelFunctions."""
    return [_create_kernel_function_from_mcp_server_tool(tool, settings) for tool in tools.tools]


def _create_kernel_function_from_mcp_server_tool(tool: Tool, settings: MCPServerExecutionSettings) -> KernelFunction:
    """Generate a KernelFunction from a tool."""

    @kernel_function(name=tool.name, description=tool.description)
    async def mcp_tool_call(**kwargs):
        async with settings.get_session() as session:
            return await session.call_tool(tool.name, arguments=kwargs)

    # Convert MCP Object in SK Object
    mcp_function: MCPTool = MCPTool.from_mcp_tool(tool)
    parameters: list[KernelParameterMetadata] = [
        _generate_kernel_parameter_from_mcp_param(mcp_parameter) for mcp_parameter in mcp_function.parameters
    ]

    return KernelFunctionFromMethod(
        method=mcp_tool_call,
        parameters=parameters,
    )


def _generate_kernel_parameter_from_mcp_param(property: MCPToolParameters) -> KernelParameterMetadata:
    """Generate a KernelParameterMetadata from an MCP Server."""
    return KernelParameterMetadata(
        name=property.name,
        type_=property.type,
        is_required=property.required,
        default_value=property.default_value,
        schema_data=property.items
        if property.items is not None and isinstance(property.items, dict)
        else {"type": f"{property.type}"}
        if property.type
        else None,
    )
