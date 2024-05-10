# Copyright (c) Microsoft. All rights reserved.

from io import BufferedReader, BytesIO
from unittest.mock import mock_open, patch

import httpx
import pytest

from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import (
    SessionsPythonTool,
)
from semantic_kernel.kernel import Kernel


def test_auth_callback():
    return "sample_token"


def test_it_can_be_instantiated(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=test_auth_callback)
    assert plugin is not None


def test_validate_endpoint(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=test_auth_callback)
    assert plugin is not None
    assert plugin.pool_management_endpoint == aca_python_sessions_unit_test_env["ACA_POOL_MANAGEMENT_ENDPOINT"]


def test_it_can_be_imported(kernel: Kernel, aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=test_auth_callback)
    assert kernel.add_plugin(plugin=plugin, plugin_name="PythonCodeInterpreter")
    assert kernel.plugins["PythonCodeInterpreter"] is not None
    assert kernel.plugins["PythonCodeInterpreter"].name == "PythonCodeInterpreter"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_call_to_container_succeeds(mock_post, aca_python_sessions_unit_test_env):
    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/python/execute/")

        mock_response = httpx.Response(
            status_code=200, json={"result": "success", "stdout": "", "stderr": ""}, request=mock_request
        )

        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=test_auth_callback)
        result = await plugin.execute_code("print('hello world')")

        assert result is not None
        mock_post.assert_awaited_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_call_to_container_fails_raises_exception(mock_post, aca_python_sessions_unit_test_env):
    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/python/execute/")

        mock_response = httpx.Response(status_code=500, request=mock_request)

        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=test_auth_callback)

        with pytest.raises(Exception):
            _ = await plugin.execute_code("print('hello world')")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_upload_file_with_local_path(mock_post, aca_python_sessions_unit_test_env):
    """Test upload_file when providing a local file path."""

    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ), patch("builtins.open", mock_open(read_data=b"file data")):
        mock_request = httpx.Request(method="POST", url="https://example.com/python/uploadFile?identifier=None")

        mock_response = httpx.Response(
            status_code=200, json={"filename": "test.txt", "bytes": 123}, request=mock_request
        )
        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

        result = await plugin.upload_file(local_file_path="test.txt", remote_file_path="uploaded_test.txt")
        assert result.filename == "test.txt"
        assert result.size_in_bytes == 123
        mock_post.assert_awaited_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_upload_file_with_buffer(mock_post, aca_python_sessions_unit_test_env):
    """Test upload_file when providing file data as a BufferedReader."""

    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/python/uploadFile?identifier=None")

        mock_response = httpx.Response(
            status_code=200, json={"filename": "buffer_file.txt", "bytes": 456}, request=mock_request
        )
        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

        data_buffer = BufferedReader(BytesIO(b"file data"))

        result = await plugin.upload_file(data=data_buffer, remote_file_path="buffer_file.txt")
        assert result.filename == "buffer_file.txt"
        assert result.size_in_bytes == 456
        mock_post.assert_awaited_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_files(mock_get, aca_python_sessions_unit_test_env):
    """Test list_files function."""

    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):

        mock_request = httpx.Request(method="GET", url="https://example.com/python/files?identifier=None")

        mock_response = httpx.Response(
            status_code=200,
            json={
                "$values": [
                    {"filename": "test1.txt", "bytes": 123},
                    {"filename": "test2.txt", "bytes": 456},
                ]
            },
            request=mock_request,
        )
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

        files = await plugin.list_files()
        assert len(files) == 2
        assert files[0].filename == "test1.txt"
        assert files[0].size_in_bytes == 123
        assert files[1].filename == "test2.txt"
        assert files[1].size_in_bytes == 456
        mock_get.assert_awaited_once()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_download_file_to_local(mock_get, aca_python_sessions_unit_test_env):
    """Test download_file when saving to a local file path."""

    async def async_return(result):
        return result

    async def mock_auth_callback():
        return "test_token"

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ), patch("builtins.open", mock_open()) as mock_file:
        mock_request = httpx.Request(
            method="GET", url="https://example.com/python/downloadFile?identifier=None&filename=remote_test.txt"
        )

        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=mock_auth_callback)

        await plugin.download_file(remote_file_path="remote_test.txt", local_file_path="local_test.txt")
        mock_get.assert_awaited_once()
        mock_file.assert_called_once_with("local_test.txt", "wb")
        mock_file().write.assert_called_once_with(b"file data")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_download_file_to_buffer(mock_get, aca_python_sessions_unit_test_env):
    """Test download_file when returning as a BufferedReader."""

    async def async_return(result):
        return result

    async def mock_auth_callback():
        return "test_token"

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(
            method="GET", url="https://example.com/python/downloadFile?identifier=None&filename=remote_test.txt"
        )

        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=mock_auth_callback)

        buffer = await plugin.download_file(remote_file_path="remote_test.txt")
        assert buffer is not None
        assert buffer.read() == b"file data"
        mock_get.assert_awaited_once()


@pytest.mark.parametrize(
    "input_code, expected_output",
    [
        # Basic whitespace removal
        ("  print('hello')  ", "print('hello')"),
        (" \n  `print('hello')`  ", "print('hello')"),
        ("`  print('hello')`", "print('hello')"),
        # Removal of 'python' keyword
        (" python print('hello') ", "print('hello')"),
        ("  Python print('hello')  ", "print('hello')"),
        ("`  python print('hello')`  ", "print('hello')"),
        ("`Python print('hello')`", "print('hello')"),
        # Mixed usage
        (" ` python print('hello')` ", "print('hello')"),
        ("   `python print('hello') `", "print('hello')"),
        # Code without any issues
        ("print('hello')", "print('hello')"),
        # Empty code
        ("", ""),
        ("` `", ""),
        ("  ", ""),
    ],
)
def test_sanitize_input(input_code, expected_output, aca_python_sessions_unit_test_env):
    """Test the `_sanitize_input` function with various inputs."""
    plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")
    sanitized_code = plugin._sanitize_input(input_code)
    assert sanitized_code == expected_output
