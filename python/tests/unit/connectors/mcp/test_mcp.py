# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import MagicMock, patch

import pytest
from mcp import ClientSession, ListToolsResult, StdioServerParameters, Tool

from semantic_kernel.connectors.mcp import (
    MCPSseServerConfig,
    MCPStdioServerConfig,
    create_plugin_from_mcp_server,
)
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError


@pytest.fixture
def list_tool_calls() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="func1",
                description="func1",
                inputSchema={
                    "properties": {
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="func2",
                description="func2",
                inputSchema={},
            ),
        ]
    )


async def test_mcp_server_config_session_initialize():
    # Test if Client can insert it's own Session
    mock_session = MagicMock(spec=ClientSession)
    config = MCPSseServerConfig(session=mock_session, url="http://localhost:8080/sse")
    async with config.get_session() as session:
        assert session is mock_session


async def test_mcp_sse_server_config_get_session():
    # Patch both the `ClientSession` and `sse_client` independently
    with (
        patch("semantic_kernel.connectors.mcp.ClientSession") as mock_client_session,
        patch("semantic_kernel.connectors.mcp.sse_client") as mock_sse_client,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_generator = MagicMock()
        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_generator.__aenter__.return_value = (mock_read, mock_write)
        mock_generator.__aexit__.return_value = (mock_read, mock_write)

        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_sse_client.return_value = mock_generator

        settings = MCPSseServerConfig(url="http://localhost:8080/sse")

        # Test the `get_session` method with ClientSession mock
        async with settings.get_session() as session:
            assert session == mock_client_session


async def test_mcp_stdio_server_config_get_session():
    # Patch both the `ClientSession` and `sse_client` independently
    with (
        patch("semantic_kernel.connectors.mcp.ClientSession") as mock_client_session,
        patch("semantic_kernel.connectors.mcp.stdio_client") as mock_stdio_client,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_generator = MagicMock()
        # Make the mock_stdio_client return an AsyncMock for the context manager
        mock_generator.__aenter__.return_value = (mock_read, mock_write)
        mock_generator.__aexit__.return_value = (mock_read, mock_write)

        # Make the mock_stdio_client return an AsyncMock for the context manager
        mock_stdio_client.return_value = mock_generator

        settings = MCPStdioServerConfig(
            command="echo",
            args=["Hello"],
        )

        # Test the `get_session` method with ClientSession mock
        async with settings.get_session() as session:
            assert session == mock_client_session


async def test_mcp_stdio_server_config_failed_get_session():
    # Patch both the `ClientSession` and `stdio_client` independently
    with (
        patch("semantic_kernel.connectors.mcp.stdio_client") as mock_stdio_client,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_generator = MagicMock()
        # Make the mock_stdio_client return an AsyncMock for the context manager
        mock_generator.__aenter__.side_effect = Exception("Connection failed")
        mock_generator.__aexit__.return_value = (mock_read, mock_write)

        # Make the mock_stdio_client return an AsyncMock for the context manager
        mock_stdio_client.return_value = mock_generator

        settings = MCPStdioServerConfig(
            command="echo",
            args=["Hello"],
        )

        # Test the `get_session` method with ClientSession mock and expect an exception
        with pytest.raises(KernelPluginInvalidConfigurationError):
            async with settings.get_session():
                pass


@patch("semantic_kernel.connectors.mcp.stdio_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_stdio(mock_session, mock_client, list_tool_calls):
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)

    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    plugin = await create_plugin_from_mcp_server(
        plugin_name="TestMCPPlugin",
        description="Test MCP Plugin",
        command="uv",
        args=["--directory", "path", "run", "file.py"],
    )
    mock_client.assert_called_once_with(
        server=StdioServerParameters(command="uv", args=["--directory", "path", "run", "file.py"])
    )
    assert plugin is not None
    assert plugin.name == "TestMCPPlugin"
    assert plugin.description == "Test MCP Plugin"
    assert plugin.functions.get("func1") is not None
    assert plugin.functions["func1"].parameters[0].name == "name"
    assert plugin.functions["func1"].parameters[0].is_required
    assert plugin.functions.get("func2") is not None
    assert len(plugin.functions["func2"].parameters) == 0


@patch("semantic_kernel.connectors.mcp.sse_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_sse(mock_session, mock_client, list_tool_calls):
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)

    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    plugin = await create_plugin_from_mcp_server(
        plugin_name="TestMCPPlugin",
        description="Test MCP Plugin",
        url="http://localhost:8080/sse",
    )
    mock_client.assert_called_once_with(url="http://localhost:8080/sse")
    assert plugin is not None
    assert plugin.name == "TestMCPPlugin"
    assert plugin.description == "Test MCP Plugin"
    assert plugin.functions.get("func1") is not None
    assert plugin.functions["func1"].parameters[0].name == "name"
    assert plugin.functions["func1"].parameters[0].is_required
    assert plugin.functions.get("func2") is not None
    assert len(plugin.functions["func2"].parameters) == 0
