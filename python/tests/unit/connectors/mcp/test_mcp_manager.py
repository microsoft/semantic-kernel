# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import ClientSession
from mcp.types import ListToolsResult, Tool

from semantic_kernel.connectors.mcp import (
    MCPClient,
    MCPToolParameters,
    _create_kernel_function_from_mcp_server_tool,
    _create_kernel_function_from_mcp_server_tools,
    _generate_kernel_parameter_from_mcp_param,
    create_function_from_mcp_server,
)
from semantic_kernel.exceptions import ServiceInvalidTypeError


def test_generate_kernel_parameter_from_mcp_function_no_items():
    test_param = MCPToolParameters(
        name="test_param",
        type="string",
        required=True,
        default_value="default_value",
        items=None,
    )

    result = _generate_kernel_parameter_from_mcp_param(test_param)
    assert result.name == "test_param"
    assert result.type_ == "string"
    assert result.is_required is True
    assert result.default_value == "default_value"
    assert result.schema_data == {"type": "string"}


def test_generate_kernel_parameter_from_mcp_function_items():
    test_param = MCPToolParameters(
        name="test_param",
        type="string",
        required=True,
        default_value="default_value",
        items={"type": "array", "items": {"type": "string"}},
    )

    result = _generate_kernel_parameter_from_mcp_param(test_param)
    assert result.name == "test_param"
    assert result.type_ == "string"
    assert result.is_required is True
    assert result.default_value == "default_value"
    assert result.schema_data == {"type": "array", "items": {"type": "string"}}


def test_create_kernel_function_from_mcp_server_tool_wrong_schema():
    test_tool = Tool(
        name="test_tool",
        description="This is a test tool",
        # Wrong schema, should contain properties & required
        inputSchema={
            "param1": {"type": "string", "required": True, "default_value": "default_value"},
            "param2": {"type": "integer", "required": False},
        },
    )

    test_settings = MCPClient(session=MagicMock(spec=ClientSession))
    with pytest.raises(ServiceInvalidTypeError):
        _create_kernel_function_from_mcp_server_tool(test_tool, test_settings)


def test_create_kernel_function_from_mcp_server_tool_missing_required():
    test_tool = Tool(
        name="test_tool",
        description="This is a test tool",
        inputSchema={
            "properties": {
                "test": {"type": "string", "default_value": "default_value"},
                "test2": {"type": "integer"},
            },
        },
    )

    test_settings = MCPClient(session=MagicMock(spec=ClientSession))
    with pytest.raises(ServiceInvalidTypeError):
        _create_kernel_function_from_mcp_server_tool(test_tool, test_settings)


def test_create_kernel_function_from_mcp_server_tool():
    test_tool = Tool(
        name="test_tool",
        description="This is a test tool",
        inputSchema={
            "properties": {
                "test": {"type": "string", "default_value": "default_value"},
                "test2": {"type": "integer"},
            },
            "required": ["test"],
        },
    )

    test_settings = MCPClient(session=MagicMock(spec=ClientSession))
    result = _create_kernel_function_from_mcp_server_tool(test_tool, test_settings)
    assert result.name == "test_tool"
    assert result.description == "This is a test tool"
    assert len(result.parameters) == 2
    assert result.parameters[0].name == "test"
    assert result.parameters[0].type_ == "string"
    assert result.parameters[0].is_required is True
    assert result.parameters[0].default_value == "default_value"
    assert result.parameters[0].schema_data == {"type": "string"}


def test_create_kernel_function_from_mcp_server_tools():
    test_tool = Tool(
        name="test_tool",
        description="This is a test tool",
        inputSchema={
            "properties": {
                "test": {"type": "string", "default_value": "default_value"},
                "test2": {"type": "integer"},
            },
            "required": ["test"],
        },
    )
    test_list_tools_result = ListToolsResult(
        tools=[test_tool, test_tool],
    )
    test_settings = MCPClient(session=MagicMock(spec=ClientSession))

    results = _create_kernel_function_from_mcp_server_tools(test_list_tools_result, test_settings)
    assert len(results) == 2
    assert results[0].name == "test_tool"
    assert results[0].parameters[0].name == "test"
    assert results[0].parameters[0].type_ == "string"
    assert results[0].parameters[0].is_required is True
    assert results[0].parameters[0].default_value == "default_value"
    assert results[0].parameters[0].schema_data == {"type": "string"}


@pytest.mark.asyncio
async def test_create_function_from_mcp_server():
    test_tool = Tool(
        name="test_tool",
        description="This is a test tool",
        inputSchema={
            "properties": {
                "test": {"type": "string", "default_value": "default_value"},
                "test2": {"type": "integer"},
            },
            "required": ["test"],
        },
    )
    test_list_tools_result = ListToolsResult(
        tools=[test_tool, test_tool],
    )
    # Mock the ServerSession
    mock_session = MagicMock(spec=ClientSession)
    mock_session.list_tools = AsyncMock(return_value=test_list_tools_result)
    settings = MCPClient(session=mock_session)

    results = await create_function_from_mcp_server(settings=settings)

    assert len(results) == 2
    assert results[0].name == "test_tool"
    assert results[0].parameters[0].name == "test"
    assert results[0].parameters[0].type_ == "string"
    assert results[0].parameters[0].is_required is True
    assert results[0].parameters[0].default_value == "default_value"
    assert results[0].parameters[0].schema_data == {"type": "string"}
