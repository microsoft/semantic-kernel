# Copyright (c) Microsoft. All rights reserved.

import logging
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import ClientSession, ListToolsResult, StdioServerParameters, Tool, types
from mcp.shared.memory import create_connected_server_and_client_session

from semantic_kernel import Kernel
from semantic_kernel.connectors.mcp import (
    MCPSsePlugin,
    MCPStdioPlugin,
    MCPStreamableHttpPlugin,
    MCPWebsocketPlugin,
    create_mcp_server_from_functions,
    create_mcp_server_from_kernel,
)
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError
from semantic_kernel.functions import KernelFunction, KernelPlugin, kernel_function


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


async def test_mcp_sampling_denied_by_consent_callback():
    sampling_consent_callback = AsyncMock(return_value=False)
    plugin = MCPSsePlugin(
        name="TestMCPPlugin",
        url="http://localhost:8080/sse",
        sampling_consent_callback=sampling_consent_callback,
    )
    params = types.CreateMessageRequestParams(
        messages=[types.SamplingMessage(role="user", content=types.TextContent(type="text", text="hello"))],
        systemPrompt="server instructions",
        maxTokens=100,
    )

    result = await plugin.sampling_callback(MagicMock(), params)

    sampling_consent_callback.assert_awaited_once_with("TestMCPPlugin", params)
    assert isinstance(result, types.ErrorData)
    assert result.message == "Sampling denied by policy."


async def test_mcp_sampling_consent_callback_error_denies_request(caplog):
    sampling_consent_callback = AsyncMock(side_effect=RuntimeError("policy failure"))
    plugin = MCPSsePlugin(
        name="TestMCPPlugin",
        url="http://localhost:8080/sse",
        sampling_consent_callback=sampling_consent_callback,
    )
    params = types.CreateMessageRequestParams(
        messages=[types.SamplingMessage(role="user", content=types.TextContent(type="text", text="hello"))],
        systemPrompt="server instructions",
        maxTokens=100,
    )

    with caplog.at_level(logging.ERROR, logger="semantic_kernel.connectors.mcp"):
        result = await plugin.sampling_callback(MagicMock(), params)

    sampling_consent_callback.assert_awaited_once_with("TestMCPPlugin", params)
    assert isinstance(result, types.ErrorData)
    assert result.message == "Sampling denied by policy."
    assert "MCP sampling consent callback failed" in caplog.text


async def test_mcp_sampling_without_consent_callback_denies_by_default(caplog):
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    params = types.CreateMessageRequestParams(
        messages=[types.SamplingMessage(role="user", content=types.TextContent(type="text", text="hello"))],
        systemPrompt="server instructions",
        maxTokens=100,
    )

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        result = await plugin.sampling_callback(MagicMock(), params)

    assert isinstance(result, types.ErrorData)
    assert result.message == "Sampling denied: no consent callback configured."
    assert "denied because no sampling consent callback was configured" in caplog.text


async def test_mcp_sampling_auto_approve_logs_warning(caplog):
    plugin = MCPSsePlugin(
        name="TestMCPPlugin",
        url="http://localhost:8080/sse",
        sampling_auto_approve=True,
    )
    params = types.CreateMessageRequestParams(
        messages=[types.SamplingMessage(role="user", content=types.TextContent(type="text", text="hello"))],
        systemPrompt="server instructions",
        maxTokens=100,
    )

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        result = await plugin.sampling_callback(MagicMock(), params)

    # No kernel configured, so the request is approved but then fails for lack of a chat service.
    assert isinstance(result, types.ErrorData)
    assert "auto-approved because sampling_auto_approve is enabled" in caplog.text


async def test_mcp_tool_and_prompt_names_do_not_shadow_plugin_attributes():
    kernel = MagicMock()
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse", kernel=kernel)
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = ListToolsResult(
        tools=[
            Tool(name="kernel", description="reserved", inputSchema={}),
            Tool(name="safe_tool", description="safe", inputSchema={}),
        ]
    )
    session.list_prompts.return_value = types.ListPromptsResult(
        prompts=[
            types.Prompt(name="session", description="reserved", arguments=[]),
            types.Prompt(name="safe_prompt", description="safe", arguments=[]),
        ]
    )
    plugin.session = session

    await plugin.load_tools()

    assert plugin.kernel is kernel
    assert hasattr(plugin, "safe_tool")

    await plugin.load_prompts()

    assert plugin.session is session
    assert hasattr(plugin, "safe_prompt")


async def test_mcp_tool_and_prompt_names_can_reload_existing_mcp_functions():
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    session = AsyncMock(spec=ClientSession)
    session.list_tools.side_effect = [
        ListToolsResult(tools=[Tool(name="safe_tool", description="first tool", inputSchema={})]),
        ListToolsResult(tools=[Tool(name="safe_tool", description="second tool", inputSchema={})]),
    ]
    session.list_prompts.side_effect = [
        types.ListPromptsResult(prompts=[types.Prompt(name="safe_prompt", description="first prompt", arguments=[])]),
        types.ListPromptsResult(prompts=[types.Prompt(name="safe_prompt", description="second prompt", arguments=[])]),
    ]
    plugin.session = session

    await plugin.load_tools()
    first_tool = plugin.safe_tool
    await plugin.load_tools()

    assert plugin.safe_tool is not first_tool
    assert plugin.safe_tool.__kernel_function_description__ == "second tool"

    await plugin.load_prompts()
    first_prompt = plugin.safe_prompt
    await plugin.load_prompts()

    assert plugin.safe_prompt is not first_prompt
    assert plugin.safe_prompt.__kernel_function_description__ == "second prompt"


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


@patch("semantic_kernel.connectors.mcp.streamablehttp_client")
def test_streamablehttp_client_forwards_zero_timeouts(mock_streamablehttp_client):
    plugin = MCPStreamableHttpPlugin(
        name="TestMCPPlugin",
        url="http://localhost:8080/mcp",
        timeout=0.0,
        sse_read_timeout=0.0,
    )

    assert plugin.get_mcp_client() is mock_streamablehttp_client.return_value

    mock_streamablehttp_client.assert_called_once_with(
        url="http://localhost:8080/mcp",
        timeout=0.0,
        sse_read_timeout=0.0,
    )


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


async def test_mcp_tool_name_collision_detected(caplog):
    """Test that tools with names that normalize to the same identifier are detected and skipped."""
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = ListToolsResult(
        tools=[
            Tool(name="read-document", description="first tool", inputSchema={}),
            Tool(name="read document", description="second tool", inputSchema={}),
        ]
    )
    plugin.session = session

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        await plugin.load_tools()

    # Only the first tool should be registered
    assert hasattr(plugin, "read-document")
    func = getattr(plugin, "read-document")
    assert func.__kernel_function_description__ == "first tool"
    # Warning should be emitted for the collision
    assert "read document" in caplog.text
    assert "already registered" in caplog.text


async def test_mcp_prompt_name_collision_detected(caplog):
    """Test that prompts with names that normalize to the same identifier are detected and skipped."""
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = ListToolsResult(tools=[])
    session.list_prompts.return_value = types.ListPromptsResult(
        prompts=[
            types.Prompt(name="get-summary", description="first prompt", arguments=[]),
            types.Prompt(name="get summary", description="second prompt", arguments=[]),
        ]
    )
    plugin.session = session

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        await plugin.load_prompts()

    # Only the first prompt should be registered
    assert hasattr(plugin, "get-summary")
    func = getattr(plugin, "get-summary")
    assert func.__kernel_function_description__ == "first prompt"
    # Warning should be emitted for the collision
    assert "get summary" in caplog.text
    assert "already registered" in caplog.text


async def test_mcp_tool_name_collision_detected_across_reload(caplog):
    """Test that a later tool reload cannot overwrite a previously registered normalized name."""
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    session = AsyncMock(spec=ClientSession)
    session.list_tools.side_effect = [
        ListToolsResult(tools=[Tool(name="read-document", description="first tool", inputSchema={})]),
        ListToolsResult(tools=[Tool(name="read document", description="second tool", inputSchema={})]),
    ]
    plugin.session = session

    await plugin.load_tools()

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        await plugin.load_tools()

    func = getattr(plugin, "read-document")
    assert func.__kernel_function_description__ == "first tool"
    assert "read document" in caplog.text
    assert "already registered" in caplog.text


async def test_mcp_prompt_does_not_replace_registered_tool_name(caplog):
    """Test that a prompt does not rebind a normalized name already registered by a tool."""
    plugin = MCPSsePlugin(name="TestMCPPlugin", url="http://localhost:8080/sse")
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = ListToolsResult(
        tools=[Tool(name="read-document", description="first tool", inputSchema={})]
    )
    session.list_prompts.return_value = types.ListPromptsResult(
        prompts=[types.Prompt(name="read document", description="second item", arguments=[])]
    )
    plugin.session = session

    await plugin.load_tools()

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        await plugin.load_prompts()

    func = getattr(plugin, "read-document")
    assert func.__kernel_function_description__ == "first tool"
    assert "read document" in caplog.text
    assert "already registered" in caplog.text


async def test_excluded_function_cannot_be_called(kernel: "Kernel"):
    """Test that excluded functions are rejected at call time, not just hidden from listing."""
    side_effect_called = False

    @kernel_function(name="public_echo")
    def public_echo(message: str) -> str:
        return f"echo: {message}"

    @kernel_function(name="secret_admin")
    def secret_admin(target: str) -> str:
        nonlocal side_effect_called
        side_effect_called = True
        return f"privileged action on {target}"

    kernel.add_function(plugin_name="tools", function=public_echo)
    kernel.add_function(plugin_name="tools", function=secret_admin)

    server = create_mcp_server_from_kernel(kernel, excluded_functions=["secret_admin"])

    # Verify the server was created with handlers
    assert types.ListToolsRequest in server.request_handlers
    assert types.CallToolRequest in server.request_handlers

    # Mock _get_cached_tool_definition to bypass SDK request context requirements
    # (normally set by a real MCP session transport)
    async def _fake_get_cached_tool_definition(tool_name):
        return None

    server._get_cached_tool_definition = _fake_get_cached_tool_definition

    # Build a proper CallToolRequest as the MCP SDK would send
    call_tool_request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name="secret_admin", arguments={}),
    )

    # The internal handler wraps our _call_tool; invoke via the registered handler
    handler = server.request_handlers[types.CallToolRequest]
    result = await handler(call_tool_request)

    # The call must fail (isError=True) with the correct error message
    assert result.root.isError is True, "Calling an excluded function should return an error"
    assert any("Unknown tool" in c.text for c in result.root.content if hasattr(c, "text")), (
        f"Expected 'Unknown tool' error, got: {result.root.content}"
    )
    assert not side_effect_called, "Excluded function's side effect should not have fired"


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("reverse_registration", [False, True])
async def test_mcp_server_duplicate_names(kernel, caplog, use_plugin_names, reverse_registration):
    calls = []

    @kernel_function(name="process_document", description="First schema")
    def first(first_id: str) -> str:
        calls.append("first")
        return first_id

    @kernel_function(name="process_document", description="Second schema")
    def second(second_id: int) -> str:
        calls.append("second")
        return str(second_id)

    registrations = [
        ("First", first, "first_id", "one", "first"),
        ("Second", second, "second_id", 2, "second"),
    ]
    if reverse_registration:
        registrations.reverse()
    for plugin_name, function, *_ in registrations:
        kernel.add_function(plugin_name, function)

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        server = kernel.as_mcp_server(**({"use_plugin_names": True} if use_plugin_names else {}))

    if use_plugin_names:
        assert not caplog.records
    else:
        assert "Skipping function" in caplog.text
        assert "First-process_document" in caplog.text
        assert "Second-process_document" in caplog.text

    retained = registrations if use_plugin_names else registrations[:1]
    async with create_connected_server_and_client_session(server) as client:
        tools = (await client.list_tools()).tools
        assert len(tools) == len(retained)
        for tool, (plugin_name, function, parameter, value, marker) in zip(tools, retained):
            expected_name = f"{plugin_name}-process_document" if use_plugin_names else "process_document"
            assert tool.name == expected_name
            assert tool.description == function.__kernel_function_description__
            assert tool.inputSchema["required"] == [parameter]
            assert set(tool.inputSchema["properties"]) == {parameter}
            result = await client.call_tool(tool.name, {parameter: value})
            assert not result.isError
            assert result.content == [types.TextContent(type="text", text=str(value))]
            assert calls[-1] == marker

        unexposed_name = "process_document" if use_plugin_names else "First-process_document"
        result = await client.call_tool(unexposed_name, {})
        assert result.isError
        assert "Unknown tool" in result.content[0].text
    assert calls == [registration[-1] for registration in retained]


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("reverse_registration", [False, True])
async def test_mcp_server_uses_registered_plugin_alias(caplog, use_plugin_names, reverse_registration):
    calls = []

    @kernel_function(name="echo", description="First schema")
    def first(message: str) -> str:
        calls.append("first")
        return message

    @kernel_function(name="echo", description="Second schema")
    def second(count: int) -> str:
        calls.append("second")
        return str(count)

    registrations = [
        ("first_alias", first, "message", "hello", "first"),
        ("second_alias", second, "count", 2, "second"),
    ]
    if reverse_registration:
        registrations.reverse()
    kernel = Kernel(
        plugins={alias: KernelPlugin(name="actual", functions=[function]) for alias, function, *_ in registrations}
    )
    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        server = kernel.as_mcp_server(use_plugin_names=use_plugin_names)

    if use_plugin_names:
        assert not caplog.records
    else:
        assert [record.getMessage() for record in caplog.records] == [
            (
                f"Skipping function '{registrations[1][0]}-echo' because MCP tool name 'echo' "
                f"is already registered by '{registrations[0][0]}-echo'."
            )
        ]

    retained = registrations if use_plugin_names else registrations[:1]
    expected_names = [f"{alias}-echo" if use_plugin_names else "echo" for alias, *_ in retained]
    async with create_connected_server_and_client_session(server) as client:
        tools = (await client.list_tools()).tools
        assert [tool.name for tool in tools] == expected_names
        for tool, (_, function, parameter, value, marker) in zip(tools, retained):
            assert tool.description == function.__kernel_function_description__
            assert tool.inputSchema["required"] == [parameter]
            assert set(tool.inputSchema["properties"]) == {parameter}
            result = await client.call_tool(tool.name, {parameter: value})
            assert not result.isError
            assert result.content == [types.TextContent(type="text", text=str(value))]
            assert calls[-1] == marker

        unexposed_names = ["actual-echo", "echo"] if use_plugin_names else ["actual-echo", "first_alias-echo"]
        for name in unexposed_names:
            result = await client.call_tool(name, {})
            assert result.isError
            assert "Unknown tool" in result.content[0].text

    assert calls == [registration[-1] for registration in retained]


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("excluded_functions", ["secret", ["secret"]])
@pytest.mark.parametrize("use_registered_alias", [False, True])
async def test_mcp_server_exclusions_use_bare_names(use_plugin_names, excluded_functions, use_registered_alias):
    calls = []

    @kernel_function
    def public() -> str:
        return "public"

    @kernel_function
    def secret() -> str:
        calls.append("secret")
        return "secret"

    kernel = Kernel(
        plugins={
            "First": KernelPlugin(name="actual" if use_registered_alias else "First", functions=[public, secret]),
            "Second": KernelPlugin(name="actual" if use_registered_alias else "Second", functions=[secret]),
        }
    )
    server = create_mcp_server_from_kernel(
        kernel, use_plugin_names=use_plugin_names, excluded_functions=excluded_functions
    )

    async with create_connected_server_and_client_session(server) as client:
        tools = (await client.list_tools()).tools
        public_name = "First-public" if use_plugin_names else "public"
        assert [tool.name for tool in tools] == [public_name]
        for name in ("secret", "First-secret", "Second-secret", "actual-secret"):
            result = await client.call_tool(name, {})
            assert result.isError
        result = await client.call_tool(public_name, {})
        assert not result.isError
    assert not calls


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("input_type", ["function", "object"])
async def test_mcp_server_from_functions_naming(use_plugin_names, input_type):
    @kernel_function
    def echo(message: str) -> str:
        return message

    class EchoPlugin:
        @kernel_function
        def echo(self, message: str) -> str:
            return message

    server = create_mcp_server_from_functions(
        KernelFunction.from_method(echo) if input_type == "function" else EchoPlugin(),
        plugin_name="Demo",
        use_plugin_names=use_plugin_names,
    )
    async with create_connected_server_and_client_session(server) as client:
        name = "Demo-echo" if use_plugin_names else "echo"
        assert [tool.name for tool in (await client.list_tools()).tools] == [name]
        result = await client.call_tool(name, {"message": "hello"})
        assert not result.isError
        assert result.content == [types.TextContent(type="text", text="hello")]


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("plugin_name", [None, "Alias"])
async def test_mcp_server_from_functions_retains_existing_plugin_name(use_plugin_names, plugin_name):
    @kernel_function
    def echo(message: str) -> str:
        return message

    plugin = KernelPlugin(name="Real", functions=[echo])
    original_function = plugin["echo"]
    server = create_mcp_server_from_functions(
        plugin, use_plugin_names=use_plugin_names, **({"plugin_name": plugin_name} if plugin_name else {})
    )

    assert plugin.name == "Real"
    assert plugin["echo"] is original_function
    assert original_function.plugin_name == "Real"
    async with create_connected_server_and_client_session(server) as client:
        name = "Real-echo" if use_plugin_names else "echo"
        assert [tool.name for tool in (await client.list_tools()).tools] == [name]
        result = await client.call_tool(name, {"message": "hello"})
        assert not result.isError
        assert result.content == [types.TextContent(type="text", text="hello")]
        for unexposed_name in ("Alias-echo", "mcp-echo"):
            result = await client.call_tool(unexposed_name, {"message": "hello"})
            assert result.isError
            assert "Unknown tool" in result.content[0].text


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("reverse_registration", [False, True])
async def test_mcp_server_from_functions_preserves_plugin_namespaces(caplog, use_plugin_names, reverse_registration):
    calls = []

    @kernel_function(name="echo", description="First schema")
    def first(message: str) -> str:
        calls.append("first")
        return message

    @kernel_function(name="echo", description="Second schema")
    def second(count: int) -> str:
        calls.append("second")
        return str(count)

    registrations = [
        (KernelPlugin(name="First", functions=[first]), "message", "hello", "first"),
        (KernelPlugin(name="Second", functions=[second]), "count", 2, "second"),
    ]
    if reverse_registration:
        registrations.reverse()
    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        server = create_mcp_server_from_functions(
            [plugin for plugin, *_ in registrations], plugin_name="Alias", use_plugin_names=use_plugin_names
        )

    if use_plugin_names:
        assert not caplog.records
    else:
        assert "Skipping function" in caplog.text
        assert "First-echo" in caplog.text
        assert "Second-echo" in caplog.text

    retained = registrations if use_plugin_names else registrations[:1]
    async with create_connected_server_and_client_session(server) as client:
        tools = (await client.list_tools()).tools
        assert [tool.name for tool in tools] == [
            f"{plugin.name}-echo" if use_plugin_names else "echo" for plugin, *_ in retained
        ]
        for tool, (plugin, parameter, value, marker) in zip(tools, retained):
            assert tool.description == plugin["echo"].description
            assert tool.inputSchema["required"] == [parameter]
            assert set(tool.inputSchema["properties"]) == {parameter}
            result = await client.call_tool(tool.name, {parameter: value})
            assert not result.isError
            assert result.content == [types.TextContent(type="text", text=str(value))]
            assert calls[-1] == marker
    assert calls == [registration[-1] for registration in retained]


@pytest.mark.parametrize("tool_name_length", [128, 129])
@pytest.mark.parametrize("use_plugin_names", [False, True])
async def test_mcp_server_tool_name_length(kernel, caplog, tool_name_length, use_plugin_names):
    @kernel_function(name="f" * (tool_name_length - (2 if use_plugin_names else 0)))
    def echo() -> str:
        return "hello"

    kernel.add_function("p", echo)
    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        server = kernel.as_mcp_server(use_plugin_names=use_plugin_names)
    assert ("exceeds the recommended 128 characters" in caplog.text) == (tool_name_length > 128)
    async with create_connected_server_and_client_session(server) as client:
        tool = (await client.list_tools()).tools[0]
        assert len(tool.name) == tool_name_length
        result = await client.call_tool(tool.name, {})
        assert not result.isError


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize("use_registered_alias", [False, True])
async def test_mcp_server_retains_advertised_function(use_plugin_names, use_registered_alias):
    @kernel_function(name="echo")
    def original(message: str) -> str:
        return f"original: {message}"

    @kernel_function(name="echo")
    def replacement(other: int) -> str:
        pytest.fail("The replacement was not advertised.")

    kernel = Kernel(
        plugins={"Demo": KernelPlugin(name="actual" if use_registered_alias else "Demo", functions=[original])}
    )
    server = kernel.as_mcp_server(use_plugin_names=use_plugin_names)
    kernel.plugins["Demo"] = KernelPlugin(name="actual" if use_registered_alias else "Demo", functions=[replacement])

    async with create_connected_server_and_client_session(server) as client:
        tool = (await client.list_tools()).tools[0]
        expected_name = "Demo-echo" if use_plugin_names else "echo"
        assert tool.name == expected_name
        assert tool.inputSchema["required"] == ["message"]
        result = await client.call_tool(expected_name, {"message": "hello"})
        assert not result.isError
        assert result.content == [types.TextContent(type="text", text="original: hello")]


@pytest.mark.parametrize("use_plugin_names", [False, True])
@pytest.mark.parametrize(
    "alias,plugin_name,exceeds_limit",
    [("p", "a" * 124, False), ("a" * 123, "actual", False), ("a" * 124, "actual", True)],
)
async def test_mcp_server_tool_name_length_uses_registered_alias(
    caplog, use_plugin_names, alias, plugin_name, exceeds_limit
):
    @kernel_function
    def echo() -> str:
        return "hello"

    kernel = Kernel(plugins={alias: KernelPlugin(name=plugin_name, functions=[echo])})
    expected_name = f"{alias}-echo" if use_plugin_names else "echo"
    with caplog.at_level(logging.WARNING, logger="semantic_kernel.connectors.mcp"):
        server = kernel.as_mcp_server(use_plugin_names=use_plugin_names)
    assert ("exceeds the recommended 128 characters" in caplog.text) == (use_plugin_names and exceeds_limit)

    async with create_connected_server_and_client_session(server) as client:
        assert [tool.name for tool in (await client.list_tools()).tools] == [expected_name]
        result = await client.call_tool(expected_name, {})
        assert not result.isError
        assert result.content == [types.TextContent(type="text", text="hello")]
