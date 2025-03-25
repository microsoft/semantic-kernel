# Copyright (c) Microsoft. All rights reserved.
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("DemoServerForTesting", "This is a demo server for testing purposes.")


@mcp.tool()
def get_secret(name: str) -> int:
    """Mocks Get Secret Name"""
    secret_value = "Test"
    return f"Secret Value : {secret_value}"


@mcp.tool()
def set_secret(name: str, value: str) -> int:
    """Mocks Set Secret Name"""
    return f"Secret Value for {name} Set"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
