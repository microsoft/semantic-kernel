# Copyright (c) Microsoft. All rights reserved.

import re
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import ClientSession, ListToolsResult, StdioServerParameters, Tool, types

from semantic_kernel.connectors.mcp import MCPSsePlugin, MCPStdioPlugin, MCPStreamableHttpPlugin, MCPWebsocketPlugin
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError

if TYPE_CHECKING:
    from semantic_kernel import Kernel


@pytest.fixture
def list_tool_calls_with_slash() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="nasa/get-astronomy-picture",
                description="func with slash",
                inputSchema={"properties": {}, "required": []},
            ),
            Tool(
                name="weird\\name with spaces",
                description="func with backslash and spaces",
                inputSchema={"properties": {}, "required": []},
            ),
        ]
    )


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


@pytest.mark.parametrize(
    "plugin_class,plugin_args",
    [
        (MCPSsePlugin, {"url": "http://localhost:8080/sse"}),
        (MCPStreamableHttpPlugin, {"url": "http://localhost:8080/mcp"}),
    ],
)
async def test_mcp_plugin_session_not_initialize(plugin_class, plugin_args):
    # Test if Client can insert it's own Session
    mock_session = AsyncMock(spec=ClientSession)
    mock_session._request_id = 0
    mock_session.initialize = AsyncMock()
    async with plugin_class(name="test", session=mock_session, **plugin_args) as plugin:
        assert plugin.session is mock_session
        assert mock_session.initialize.called


@pytest.mark.parametrize(
    "plugin_class,plugin_args",
    [
        (MCPSsePlugin, {"url": "http://localhost:8080/sse"}),
        (MCPStreamableHttpPlugin, {"url": "http://localhost:8080/mcp"}),
    ],
)
async def test_mcp_plugin_session_initialized(plugin_class, plugin_args):
    # Test if Client can insert it's own initialized Session
    mock_session = AsyncMock(spec=ClientSession)
    mock_session._request_id = 1
    mock_session.initialize = AsyncMock()
    async with plugin_class(name="test", session=mock_session, **plugin_args) as plugin:
        assert plugin.session is mock_session
        assert not mock_session.initialize.called


async def test_mcp_plugin_failed_get_session():
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

        with pytest.raises(KernelPluginInvalidConfigurationError):
            async with MCPStdioPlugin(
                name="test",
                command="echo",
                args=["Hello"],
            ):
                pass


@patch("semantic_kernel.connectors.mcp.stdio_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_stdio(mock_session, mock_client, list_tool_calls, kernel: "Kernel"):
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)

    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    async with MCPStdioPlugin(
        name="TestMCPPlugin",
        description="Test MCP Plugin",
        command="uv",
        args=["--directory", "path", "run", "file.py"],
    ) as plugin:
        mock_client.assert_called_once_with(
            server=StdioServerParameters(command="uv", args=["--directory", "path", "run", "file.py"])
        )
        loaded_plugin = kernel.add_plugin(plugin)
        assert loaded_plugin is not None
        assert loaded_plugin.name == "TestMCPPlugin"
        assert loaded_plugin.description == "Test MCP Plugin"
        assert loaded_plugin.functions.get("func1") is not None
        assert loaded_plugin.functions["func1"].parameters[0].name == "name"
        assert loaded_plugin.functions["func1"].parameters[0].is_required
        assert loaded_plugin.functions.get("func2") is not None
        assert len(loaded_plugin.functions["func2"].parameters) == 0


@patch("semantic_kernel.connectors.mcp.websocket_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_websocket(mock_session, mock_client, list_tool_calls, kernel: "Kernel"):
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)

    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    async with MCPWebsocketPlugin(
        name="TestMCPPlugin",
        description="Test MCP Plugin",
        url="http://localhost:8080/websocket",
    ) as plugin:
        mock_client.assert_called_once_with(url="http://localhost:8080/websocket")
        loaded_plugin = kernel.add_plugin(plugin)
        assert loaded_plugin is not None
        assert loaded_plugin.name == "TestMCPPlugin"
        assert loaded_plugin.description == "Test MCP Plugin"
        assert loaded_plugin.functions.get("func1") is not None
        assert loaded_plugin.functions["func1"].parameters[0].name == "name"
        assert loaded_plugin.functions["func1"].parameters[0].is_required
        assert loaded_plugin.functions.get("func2") is not None
        assert len(loaded_plugin.functions["func2"].parameters) == 0


@patch("semantic_kernel.connectors.mcp.sse_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_sse(mock_session, mock_client, list_tool_calls, kernel: "Kernel"):
    mock_read = MagicMock()
    mock_write = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)

    # Make the mock_stdio_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    async with MCPSsePlugin(
        name="TestMCPPlugin",
        description="Test MCP Plugin",
        url="http://localhost:8080/sse",
    ) as plugin:
        mock_client.assert_called_once_with(url="http://localhost:8080/sse")
        loaded_plugin = kernel.add_plugin(plugin)
        assert loaded_plugin is not None
        assert loaded_plugin.name == "TestMCPPlugin"
        assert loaded_plugin.description == "Test MCP Plugin"
        assert loaded_plugin.functions.get("func1") is not None
        assert loaded_plugin.functions["func1"].parameters[0].name == "name"
        assert loaded_plugin.functions["func1"].parameters[0].is_required
        assert loaded_plugin.functions.get("func2") is not None
        assert len(loaded_plugin.functions["func2"].parameters) == 0


@patch("semantic_kernel.connectors.mcp.streamablehttp_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_with_kwargs_streamablehttp(mock_session, mock_client, list_tool_calls, kernel: "Kernel"):
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_callback = MagicMock()

    mock_generator = MagicMock()
    # Make the mock_streamablehttp_client return an AsyncMock for the context manager
    mock_generator.__aenter__.return_value = (mock_read, mock_write, mock_callback)
    mock_generator.__aexit__.return_value = (mock_read, mock_write, mock_callback)

    # Make the mock_streamablehttp_client return an AsyncMock for the context manager
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls
    async with MCPStreamableHttpPlugin(
        name="TestMCPPlugin",
        description="Test MCP Plugin",
        url="http://localhost:8080/mcp",
    ) as plugin:
        mock_client.assert_called_once_with(url="http://localhost:8080/mcp")
        loaded_plugin = kernel.add_plugin(plugin)
        assert loaded_plugin is not None
        assert loaded_plugin.name == "TestMCPPlugin"
        assert loaded_plugin.description == "Test MCP Plugin"
        assert loaded_plugin.functions.get("func1") is not None
        assert loaded_plugin.functions["func1"].parameters[0].name == "name"
        assert loaded_plugin.functions["func1"].parameters[0].is_required
        assert loaded_plugin.functions.get("func2") is not None
        assert len(loaded_plugin.functions["func2"].parameters) == 0


async def test_kernel_as_mcp_server(kernel: "Kernel", decorated_native_function, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class, "test")
    kernel.add_functions("test", [decorated_native_function])
    server = kernel.as_mcp_server()
    assert server is not None
    assert types.PingRequest in server.request_handlers
    assert types.ListToolsRequest in server.request_handlers
    assert types.CallToolRequest in server.request_handlers
    assert server.name == "Semantic Kernel MCP Server"


@patch("semantic_kernel.connectors.mcp.sse_client")
@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_mcp_tool_name_normalization(mock_session, mock_client, list_tool_calls_with_slash, kernel: "Kernel"):
    """Test that MCP tool names with illegal characters are normalized."""
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_generator = MagicMock()
    mock_generator.__aenter__.return_value = (mock_read, mock_write)
    mock_generator.__aexit__.return_value = (mock_read, mock_write)
    mock_client.return_value = mock_generator
    mock_session.return_value.__aenter__.return_value.list_tools.return_value = list_tool_calls_with_slash

    async with MCPSsePlugin(
        name="TestMCPPlugin",
        description="Test MCP Plugin",
        url="http://localhost:8080/sse",
    ) as plugin:
        loaded_plugin = kernel.add_plugin(plugin)
        # The normalized names:
        assert "nasa-get-astronomy-picture" in loaded_plugin.functions
        assert "weird-name-with-spaces" in loaded_plugin.functions
        # They should not exist with their original (invalid) names:
        assert "nasa/get-astronomy-picture" not in loaded_plugin.functions
        assert "weird\\name with spaces" not in loaded_plugin.functions

        normalized_names = list(loaded_plugin.functions.keys())
        for name in normalized_names:
            assert re.match(r"^[A-Za-z0-9_.-]+$", name)


@patch("semantic_kernel.connectors.mcp.ClientSession")
async def test_mcp_normalization_function(mock_session, list_tool_calls_with_slash):
    """Unit test for the normalize_mcp_name function (should exist in codebase)."""
    from semantic_kernel.connectors.mcp import _normalize_mcp_name

    assert _normalize_mcp_name("nasa/get-astronomy-picture") == "nasa-get-astronomy-picture"
    assert _normalize_mcp_name("weird\\name with spaces") == "weird-name-with-spaces"
    assert _normalize_mcp_name("simple_name") == "simple_name"
    assert _normalize_mcp_name("Name-With.Dots_And-Hyphens") == "Name-With.Dots_And-Hyphens"
