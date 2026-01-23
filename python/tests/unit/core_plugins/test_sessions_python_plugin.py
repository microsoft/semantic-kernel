# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import mock_open, patch

import httpx
import pytest
from httpx import HTTPStatusError

from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import (
    SESSIONS_API_VERSION,
    SessionsPythonTool,
)
from semantic_kernel.core_plugins.sessions_python_tool.sessions_remote_file_metadata import SessionsRemoteFileMetadata
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.kernel import Kernel


def auth_callback_test():
    return "sample_token"


def test_it_can_be_instantiated(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    assert plugin is not None


def test_validate_endpoint(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    assert plugin is not None
    assert str(plugin.pool_management_endpoint) == aca_python_sessions_unit_test_env["ACA_POOL_MANAGEMENT_ENDPOINT"]


@pytest.mark.parametrize(
    "base_url, endpoint, params, expected_url",
    [
        (
            "http://example.com",
            "api/resource",
            {"param1": "value1", "param2": "value2"},
            f"http://example.com/api/resource?param1=value1&param2=value2&api-version={SESSIONS_API_VERSION}",
        ),
        (
            "http://example.com/",
            "api/resource",
            {"param1": "value1"},
            f"http://example.com/api/resource?param1=value1&api-version={SESSIONS_API_VERSION}",
        ),
        (
            "http://example.com",
            "api/resource/",
            {"param1": "value1", "param2": "value2"},
            f"http://example.com/api/resource?param1=value1&param2=value2&api-version={SESSIONS_API_VERSION}",
        ),
        (
            "http://example.com/",
            "api/resource/",
            {"param1": "value1"},
            f"http://example.com/api/resource?param1=value1&api-version={SESSIONS_API_VERSION}",
        ),
        (
            "http://example.com",
            "api/resource",
            {},
            f"http://example.com/api/resource?api-version={SESSIONS_API_VERSION}",
        ),
        (
            "http://example.com/",
            "api/resource",
            {},
            f"http://example.com/api/resource?api-version={SESSIONS_API_VERSION}",
        ),
    ],
)
def test_build_url_with_version(base_url, endpoint, params, expected_url, aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    result = plugin._build_url_with_version(base_url, endpoint, params)
    assert result == expected_url


@pytest.mark.parametrize(
    "override_env_param_dict",
    [
        {"ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint/python/execute/"},
        {"ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint/python/execute"},
    ],
    indirect=True,
)
def test_validate_endpoint_with_execute(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    assert plugin is not None
    assert "/python/execute" not in str(plugin.pool_management_endpoint)


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint"}],
    indirect=True,
)
def test_validate_endpoint_no_final_slash(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    assert plugin is not None
    assert str(plugin.pool_management_endpoint) == "https://test.endpoint/"


@pytest.mark.parametrize("exclude_list", [["ACA_POOL_MANAGEMENT_ENDPOINT"]], indirect=True)
def test_validate_settings_fail(aca_python_sessions_unit_test_env):
    with pytest.raises(FunctionInitializationError):
        SessionsPythonTool(
            auth_callback=auth_callback_test,
            env_file_path="test.env",
        )


def test_it_can_be_imported(kernel: Kernel, aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    assert kernel.add_plugin(plugin=plugin, plugin_name="PythonCodeInterpreter")
    assert kernel.get_plugin(plugin_name="PythonCodeInterpreter") is not None
    assert kernel.get_plugin(plugin_name="PythonCodeInterpreter").name == "PythonCodeInterpreter"


@patch("httpx.AsyncClient.post")
async def test_call_to_container_succeeds(mock_post, aca_python_sessions_unit_test_env):
    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/code/execute/")

        mock_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "properties": {
                    "$id": "2",
                    "status": "Success",
                    "stdout": "",
                    "stderr": "",
                    "result": "even_numbers = [2 * i for i in range(1, 11)]\\nprint(even_numbers)",
                    "executionTimeInMilliseconds": 12,
                },
            },
            request=mock_request,
        )

        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=auth_callback_test)
        result = await plugin.execute_code("print('hello world')")

        assert result is not None
        mock_post.assert_awaited_once()


@patch("httpx.AsyncClient.post")
async def test_call_to_container_fails_raises_exception(mock_post, aca_python_sessions_unit_test_env):
    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/code/execute/")

        mock_response = httpx.Response(status_code=500, request=mock_request)

        mock_post.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=auth_callback_test)

        with pytest.raises(Exception):
            _ = await plugin.execute_code("print('hello world')")


async def test_empty_call_to_container_fails_raises_exception(aca_python_sessions_unit_test_env):
    plugin = SessionsPythonTool(auth_callback=auth_callback_test)
    with pytest.raises(FunctionExecutionException):
        await plugin.execute_code(code="")


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
async def test_upload_file_with_local_path(mock_post, mock_get, aca_python_sessions_unit_test_env, tmp_path):
    """Test upload_file when providing a local file path."""

    async def async_return(result):
        return result

    # Create a real file in a temp directory for the test
    test_file = tmp_path / "hello.py"
    test_file.write_bytes(b"file data")

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/files/upload?identifier=None")
        mock_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [],
            },
            request=mock_request,
        )
        mock_post.return_value = await async_return(mock_response)

        mock_get_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")
        mock_get_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [
                    {
                        "$id": "2",
                        "properties": {
                            "$id": "3",
                            "filename": "hello.py",
                            "size": 123,
                            "lastModifiedTime": "2024-07-02T19:29:23.4369699Z",
                        },
                    },
                ],
            },
            request=mock_get_request,
        )
        mock_get.return_value = await async_return(mock_get_response)

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            env_file_path="test.env",
            allowed_upload_directories={str(tmp_path)},
        )

        result = await plugin.upload_file(local_file_path=str(test_file), remote_file_path="hello.py")
        assert result.filename == "hello.py"
        assert result.size_in_bytes == 123
        assert result.full_path == "/mnt/data/hello.py"
        mock_post.assert_awaited_once()


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
async def test_upload_file_with_local_path_and_no_remote(
    mock_post, mock_get, aca_python_sessions_unit_test_env, tmp_path
):
    """Test upload_file when providing a local file path."""

    async def async_return(result):
        return result

    # Create a real file in a temp directory for the test
    test_file = tmp_path / "hello.py"
    test_file.write_bytes(b"file data")

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_post_request = httpx.Request(method="POST", url="https://example.com/files/upload?identifier=None")
        mock_post_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [],
            },
            request=mock_post_request,
        )
        mock_post.return_value = await async_return(mock_post_response)

        mock_get_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")
        mock_get_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [
                    {
                        "$id": "2",
                        "properties": {
                            "$id": "3",
                            "filename": "hello.py",
                            "size": 123,
                            "lastModifiedTime": "2024-07-02T19:29:23.4369699Z",
                        },
                    },
                ],
            },
            request=mock_get_request,
        )
        mock_get.return_value = await async_return(mock_get_response)

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            env_file_path="test.env",
            allowed_upload_directories={str(tmp_path)},
        )

        result = await plugin.upload_file(local_file_path=str(test_file))
        assert result.filename == "hello.py"
        assert result.size_in_bytes == 123
        mock_post.assert_awaited_once()


@patch("httpx.AsyncClient.post")
async def test_upload_file_throws_exception(mock_post, aca_python_sessions_unit_test_env, tmp_path):
    """Test throwing exception during file upload."""

    async def async_raise_http_error(*args, **kwargs):
        mock_request = httpx.Request(method="POST", url="https://example.com/files/upload")
        mock_response = httpx.Response(status_code=500, request=mock_request)
        raise HTTPStatusError("Server Error", request=mock_request, response=mock_response)

    # Create a real file in a temp directory for the test
    test_file = tmp_path / "hello.py"
    test_file.write_bytes(b"file data")

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_post.side_effect = async_raise_http_error

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            env_file_path="test.env",
            allowed_upload_directories={str(tmp_path)},
        )

        with pytest.raises(
            FunctionExecutionException, match="Upload failed with status code 500 and error: Internal Server Error"
        ):
            await plugin.upload_file(local_file_path=str(test_file))
        mock_post.assert_awaited_once()


@pytest.mark.parametrize(
    "input_remote_file_path, expected_remote_file_path",
    [
        ("uploaded_test.txt", "/mnt/data/uploaded_test.txt"),
        ("/mnt/data/input.py", "/mnt/data/input.py"),
    ],
)
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
async def test_upload_file_with_buffer(
    mock_post,
    mock_get,
    input_remote_file_path,
    expected_remote_file_path,
    aca_python_sessions_unit_test_env,
    tmp_path,
):
    """Test upload_file when providing file data as a BufferedReader."""

    async def async_return(result):
        return result

    # Create a real file in a temp directory for the test
    test_file = tmp_path / "file.py"
    test_file.write_text("print('hello, world~')")

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/files/upload?identifier=None")
        mock_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [],
            },
            request=mock_request,
        )
        mock_post.return_value = await async_return(mock_response)

        mock_get_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")
        mock_get_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [
                    {
                        "$id": "2",
                        "properties": {
                            "$id": "3",
                            "filename": expected_remote_file_path,
                            "size": 456,
                            "lastModifiedTime": "2024-07-02T19:29:23.4369699Z",
                        },
                    },
                ],
            },
            request=mock_get_request,
        )
        mock_get.return_value = await async_return(mock_get_response)

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            allowed_upload_directories={str(tmp_path)},
        )

        result = await plugin.upload_file(local_file_path=str(test_file), remote_file_path=input_remote_file_path)
        assert result.filename == expected_remote_file_path
        assert result.size_in_bytes == 456
        mock_post.assert_awaited_once()


async def test_upload_file_fail_with_no_local_path(aca_python_sessions_unit_test_env):
    """Test upload_file when not providing a local file path throws an exception."""

    plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")
    with pytest.raises(FunctionExecutionException):
        await plugin.upload_file(
            local_file_path=None,
            remote_file_path="uploaded_test.txt",
        )


@patch("httpx.AsyncClient.get")
async def test_list_files(mock_get, aca_python_sessions_unit_test_env):
    """Test list_files function."""

    async def async_return(result):
        return result

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")

        mock_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [
                    {
                        "$id": "2",
                        "properties": {
                            "$id": "3",
                            "filename": "hello.py",
                            "size": 123,
                            "lastModifiedTime": "2024-07-02T19:29:23.4369699Z",
                        },
                    },
                    {
                        "$id": "4",
                        "properties": {
                            "$id": "5",
                            "filename": "world.py",
                            "size": 456,
                            "lastModifiedTime": "2024-07-02T19:29:38.1329088Z",
                        },
                    },
                ],
            },
            request=mock_request,
        )
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

        files = await plugin.list_files()
        assert len(files) == 2
        assert files[0].filename == "hello.py"
        assert files[0].size_in_bytes == 123
        assert files[1].filename == "world.py"
        assert files[1].size_in_bytes == 456
        mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_list_files_throws_exception(mock_get, aca_python_sessions_unit_test_env):
    """Test throwing exception during list files."""

    async def async_raise_http_error(*args, **kwargs):
        mock_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")
        mock_response = httpx.Response(status_code=500, request=mock_request)
        raise HTTPStatusError("Server Error", request=mock_request, response=mock_response)

    with (
        patch(
            "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
            return_value="test_token",
        ),
    ):
        mock_get.side_effect = async_raise_http_error

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            env_file_path="test.env",
        )

        with pytest.raises(
            FunctionExecutionException, match="List files failed with status code 500 and error: Internal Server Error"
        ):
            await plugin.list_files()
        mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_download_file_to_local(mock_get, aca_python_sessions_unit_test_env, tmp_path):
    """Test download_file when saving to a local file path."""

    async def async_return(result):
        return result

    async def mock_auth_callback():
        return "test_token"

    local_file = tmp_path / "local_test.txt"

    with (
        patch(
            "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
            return_value="test_token",
        ),
        patch("builtins.open", mock_open()) as mock_file,
    ):
        mock_request = httpx.Request(
            method="GET",
            url="https://example.com/python/files/content/remote_text.txt?identifier=None&filename=remote_test.txt",
        )

        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(
            auth_callback=mock_auth_callback,
            env_file_path="test.env",
        )

        await plugin.download_file(remote_file_name="remote_test.txt", local_file_path=str(local_file))
        mock_get.assert_awaited_once()
        # Path is canonicalized via os.path.realpath()
        mock_file.assert_called_once_with(str(local_file), "wb")
        mock_file().write.assert_called_once_with(b"file data")


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
            method="GET",
            url="https://example.com/files/content/remote_test.txt?identifier=None&filename=remote_test.txt",
        )

        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(auth_callback=mock_auth_callback)

        buffer = await plugin.download_file(remote_file_name="remote_test.txt")
        assert buffer is not None
        assert buffer.read() == b"file data"
        mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_download_file_throws_exception(mock_get, aca_python_sessions_unit_test_env):
    """Test throwing exception during download file."""

    async def async_raise_http_error(*args, **kwargs):
        mock_request = httpx.Request(
            method="GET", url="https://example.com/files/content/remote_test.txt?identifier=None"
        )
        mock_response = httpx.Response(status_code=500, request=mock_request)
        raise HTTPStatusError("Server Error", request=mock_request, response=mock_response)

    with (
        patch(
            "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
            return_value="test_token",
        ),
    ):
        mock_get.side_effect = async_raise_http_error

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            env_file_path="test.env",
        )

        with pytest.raises(
            FunctionExecutionException, match="Download failed with status code 500 and error: Internal Server Error"
        ):
            await plugin.download_file(remote_file_name="remote_test.txt")
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


async def test_auth_token(aca_python_sessions_unit_test_env):
    async def token_cb():
        return "sample_token"

    plugin = SessionsPythonTool(auth_callback=token_cb)
    assert await plugin._ensure_auth_token() == "sample_token"


async def test_auth_token_fail(aca_python_sessions_unit_test_env):
    async def token_cb():
        raise ValueError("Could not get token.")

    plugin = SessionsPythonTool(auth_callback=token_cb)
    with pytest.raises(
        FunctionExecutionException, match="Failed to retrieve the client auth token with message: Could not get token."
    ):
        await plugin._ensure_auth_token()


@pytest.mark.parametrize(
    "filename, expected_full_path",
    [
        ("/mnt/data/testfile.txt", "/mnt/data/testfile.txt"),
        ("testfile.txt", "/mnt/data/testfile.txt"),
    ],
)
def test_full_path(filename, expected_full_path):
    metadata = SessionsRemoteFileMetadata(filename=filename, size_in_bytes=123)
    assert metadata.full_path == expected_full_path


# region Tests for File Operations


async def test_upload_file_denied_when_no_allowed_directories(aca_python_sessions_unit_test_env):
    """Test that upload_file raises an exception when allowed_upload_directories is not configured."""
    plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

    with pytest.raises(FunctionExecutionException, match="File upload is disabled"):
        await plugin.upload_file(local_file_path="/some/path/file.txt")


async def test_upload_file_denied_outside_allowed_directories(aca_python_sessions_unit_test_env, tmp_path):
    """Test that upload_file raises an exception when path is outside allowed directories."""
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()

    plugin = SessionsPythonTool(
        auth_callback=lambda: "sample_token",
        allowed_upload_directories={str(allowed_dir)},
    )

    with pytest.raises(FunctionExecutionException, match="Access denied"):
        await plugin.upload_file(local_file_path="/etc/passwd")


async def test_upload_file_path_traversal_blocked(aca_python_sessions_unit_test_env, tmp_path):
    """Test that path traversal attacks are blocked."""
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()

    plugin = SessionsPythonTool(
        auth_callback=lambda: "sample_token",
        allowed_upload_directories={str(allowed_dir)},
    )

    # Attempt path traversal
    traversal_path = str(allowed_dir / ".." / ".." / "etc" / "passwd")

    with pytest.raises(FunctionExecutionException, match="Access denied"):
        await plugin.upload_file(local_file_path=traversal_path)


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
async def test_upload_file_succeeds_within_allowed_directory(
    mock_post, mock_get, aca_python_sessions_unit_test_env, tmp_path
):
    """Test that upload_file succeeds when path is within allowed directories."""

    async def async_return(result):
        return result

    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    test_file = allowed_dir / "test.txt"
    test_file.write_text("test content")

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="POST", url="https://example.com/files/upload?identifier=None")
        mock_response = httpx.Response(
            status_code=200,
            json={"$id": "1", "value": []},
            request=mock_request,
        )
        mock_post.return_value = await async_return(mock_response)

        mock_get_request = httpx.Request(method="GET", url="https://example.com/files?identifier=None")
        mock_get_response = httpx.Response(
            status_code=200,
            json={
                "$id": "1",
                "value": [
                    {
                        "$id": "2",
                        "properties": {
                            "$id": "3",
                            "filename": "test.txt",
                            "size": 12,
                            "lastModifiedTime": "2024-07-02T19:29:23.4369699Z",
                        },
                    },
                ],
            },
            request=mock_get_request,
        )
        mock_get.return_value = await async_return(mock_get_response)

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            allowed_upload_directories={str(allowed_dir)},
        )

        result = await plugin.upload_file(local_file_path=str(test_file))
        assert result.filename == "test.txt"
        mock_post.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_download_file_works_without_allowed_directories(mock_get, aca_python_sessions_unit_test_env, tmp_path):
    """Test that download_file works without restrictions when allowed_download_directories is None."""

    async def async_return(result):
        return result

    local_file = tmp_path / "downloaded.txt"

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="GET", url="https://example.com/files/content/remote.txt")
        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        # No allowed_download_directories configured - should work (permissive by default)
        plugin = SessionsPythonTool(auth_callback=lambda: "sample_token")

        await plugin.download_file(remote_file_name="remote.txt", local_file_path=str(local_file))
        assert local_file.read_bytes() == b"file data"
        mock_get.assert_awaited_once()


async def test_download_file_denied_outside_allowed_directories(aca_python_sessions_unit_test_env, tmp_path):
    """Test that download_file raises an exception when path is outside allowed directories."""
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    plugin = SessionsPythonTool(
        auth_callback=lambda: "sample_token",
        allowed_download_directories={str(allowed_dir)},
    )

    with (
        patch(
            "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
            return_value="test_token",
        ),
        patch("httpx.AsyncClient.get") as mock_get,
    ):

        async def async_return(result):
            return result

        mock_request = httpx.Request(method="GET", url="https://example.com/files/content/remote.txt")
        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        with pytest.raises(FunctionExecutionException, match="Access denied"):
            await plugin.download_file(
                remote_file_name="remote.txt",
                local_file_path=str(outside_dir / "output.txt"),
            )


@patch("httpx.AsyncClient.get")
async def test_download_file_succeeds_within_allowed_directory(mock_get, aca_python_sessions_unit_test_env, tmp_path):
    """Test that download_file succeeds when path is within allowed directories."""

    async def async_return(result):
        return result

    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    local_file = allowed_dir / "downloaded.txt"

    with patch(
        "semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin.SessionsPythonTool._ensure_auth_token",
        return_value="test_token",
    ):
        mock_request = httpx.Request(method="GET", url="https://example.com/files/content/remote.txt")
        mock_response = httpx.Response(status_code=200, content=b"file data", request=mock_request)
        mock_get.return_value = await async_return(mock_response)

        plugin = SessionsPythonTool(
            auth_callback=lambda: "sample_token",
            allowed_download_directories={str(allowed_dir)},
        )

        await plugin.download_file(remote_file_name="remote.txt", local_file_path=str(local_file))
        assert local_file.read_bytes() == b"file data"
        mock_get.assert_awaited_once()


def test_allowed_directories_accepts_list(aca_python_sessions_unit_test_env):
    """Test that allowed directories can be passed as a list and are converted to a set."""
    plugin = SessionsPythonTool(
        auth_callback=lambda: "sample_token",
        allowed_upload_directories=["/path/one", "/path/two"],
        allowed_download_directories=["/path/three"],
    )

    assert plugin.allowed_upload_directories == {"/path/one", "/path/two"}
    assert plugin.allowed_download_directories == {"/path/three"}


# endregion
