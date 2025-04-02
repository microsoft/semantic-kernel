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
    assert plugin.functions.get("get_name") is not None
    assert plugin.functions["get_name"].parameters[0].name == "name"
    assert plugin.functions["get_name"].parameters[0].type_ == "string"
    assert plugin.functions["get_name"].parameters[0].is_required
    assert plugin.functions.get("set_name") is not None

    kernel.add_plugin(plugin)

    result = await plugin.functions["get_name"].invoke(kernel, arguments=KernelArguments(name="test"))
    assert "test: Test" in result.value
