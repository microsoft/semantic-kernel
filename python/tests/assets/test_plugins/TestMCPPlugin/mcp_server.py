# Copyright (c) Microsoft. All rights reserved.

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("DemoServerForTesting", "This is a demo server for testing purposes.")


@mcp.tool()
def get_name(name: str) -> str:
    """Mocks Get Name"""
    secret_value = "Test"
    return f"{name}: {secret_value}"


@mcp.tool()
def set_name(name: str, value: str) -> str:
    """Mocks Set Name"""
    return f"Value for {name} Set"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
