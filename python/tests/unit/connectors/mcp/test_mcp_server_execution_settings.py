# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import MagicMock, patch

import pytest
from mcp import ClientSession

from semantic_kernel.connectors.mcp.mcp_server_execution_settings import (
    MCPServerExecutionSettings,
    MCPSseServerExecutionSettings,
    MCPStdioServerExecutionSettings,
)


@pytest.mark.asyncio
async def test_mcp_client_session_settings_initialize():
    # Test if Client can insert it's own Session
    mock_session = MagicMock(spec=ClientSession)
    settings = MCPServerExecutionSettings(session=mock_session)
    async with settings.get_session() as session:
        assert session is mock_session


@pytest.mark.asyncio
async def test_mcp_sse_server_settings_initialize_session():
    # Patch both the `ClientSession` and `sse_client` independently
    with (
        patch("semantic_kernel.connectors.mcp.mcp_server_execution_settings.ClientSession") as mock_client_session,
        patch("semantic_kernel.connectors.mcp.mcp_server_execution_settings.sse_client") as mock_sse_client,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_generator = MagicMock()
        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_generator.__aenter__.return_value = (mock_read, mock_write)
        mock_generator.__aexit__.return_value = (mock_read, mock_write)

        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_sse_client.return_value = mock_generator

        settings = MCPSseServerExecutionSettings(url="http://localhost:8080/sse")

        # Test the `get_session` method with ClientSession mock
        async with settings.get_session() as session:
            assert session == mock_client_session


@pytest.mark.asyncio
async def test_mcp_stdio_server_settings_initialize_session():
    # Patch both the `ClientSession` and `sse_client` independently
    with (
        patch("semantic_kernel.connectors.mcp.mcp_server_execution_settings.ClientSession") as mock_client_session,
        patch("semantic_kernel.connectors.mcp.mcp_server_execution_settings.stdio_client") as mock_stdio_client,
    ):
        mock_read = MagicMock()
        mock_write = MagicMock()

        mock_generator = MagicMock()
        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_generator.__aenter__.return_value = (mock_read, mock_write)
        mock_generator.__aexit__.return_value = (mock_read, mock_write)

        # Make the mock_sse_client return an AsyncMock for the context manager
        mock_stdio_client.return_value = mock_generator

        settings = MCPStdioServerExecutionSettings(
            command="echo",
            args=["Hello"],
        )

        # Test the `get_session` method with ClientSession mock
        async with settings.get_session() as session:
            assert session == mock_client_session
