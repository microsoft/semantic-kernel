# Copyright (c) Microsoft. All rights reserved.


import os
from typing import TYPE_CHECKING

from semantic_kernel.connectors.mcp import MCPStdioServerConfig, create_plugin_from_mcp_server
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel import Kernel


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
    assert len(plugin.functions) == 2

    kernel.add_plugin(plugin)

    result = await plugin.functions["echo_tool"].invoke(kernel, arguments=KernelArguments(message="test"))
    assert "Tool echo: test" in result.value[0].text

    result = await plugin.functions["echo_prompt"].invoke(kernel, arguments=KernelArguments(message="test"))
    assert "test" in result.value[0].content
