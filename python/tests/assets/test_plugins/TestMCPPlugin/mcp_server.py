# Copyright (c) Microsoft. All rights reserved.

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Echo")


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"


@mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message as a tool"""
    return f"Tool echo: {message}"


@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"


@mcp.tool()
def get_names() -> str:
    """Mocks Get Names"""
    return "Names: name1, name2, name3"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
