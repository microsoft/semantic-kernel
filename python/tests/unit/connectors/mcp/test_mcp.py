# Copyright (c) Microsoft. All rights reserved.
import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from mcp import ClientSession

from semantic_kernel.connectors.mcp import (
    MCPSseServerConfig,
    MCPStdioServerConfig,
    create_plugin_from_mcp_server,
)
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel import Kernel


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


async def test_from_mcp(kernel: "Kernel"):
    mcp_server_path = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins", "TestMCPPlugin")
    mcp_server_file = "mcp_server.py"
    config = MCPStdioServerConfig(
        command="uv",
        args=["--directory", mcp_server_path, "run", mcp_server_file],
    )

    plugin = await create_plugin_from_mcp_server(
        plugin_name="TestMCPPlugin",
        description="Test MCP Plugin",
        server_config=config,
    )

    assert plugin is not None
    assert plugin.name == "TestMCPPlugin"
    assert plugin.functions.get("get_name") is not None
    assert plugin.functions.get("set_name") is not None

    kernel.add_plugin(plugin)

    result = await plugin.functions["get_name"].invoke(kernel, arguments=KernelArguments(name="test"))
    assert result.value == "test: Test"
