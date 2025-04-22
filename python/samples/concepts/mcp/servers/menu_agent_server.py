# /// script # noqa: CPY001
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import argparse
import logging
from typing import Annotated, Any, Literal

import anyio

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)

"""
This sample demonstrates how to expose an Agent as a MCP server.

To run this sample, set up your MCP host (like Claude Desktop or VSCode Github Copilot Agents)
with the following configuration:
```json
{
    "mcpServers": {
        "sk": {
            "command": "uv",
            "args": [
                "--directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server",
                "run",
                "agent_mcp_server.py"
            ],
            "env": {
                "AZURE_AI_AGENT_PROJECT_CONNECTION_STRING": "<your azure connection string>",
                "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME": "<your azure model deployment name>",
            }
        }
    }
}
```
Alternatively, you can run this as a SSE server, by setting the same environment variables as above, 
and running the following command:
```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server \
run agent_mcp_server.py --transport sse --port 8000
```
This will start a server that listens for incoming requests on port 8000.

In both cases, uv will make sure to install semantic-kernel with the mcp extra for you in a temporary venv.
"""


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the Semantic Kernel MCP server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport method to use (default: stdio).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to use for SSE transport (required if transport is 'sse').",
    )
    return parser.parse_args()


# Define a simple plugin for the sample
class RestaurantPlugin:
    """A sample Menu Plugin used for the sample."""

    @kernel_function(description="List the available restaurants.")
    def list_restaurants(self) -> Annotated[str, "Returns a list of available restaurants."]:
        return """
            1. The Farm: a classic steakhouse with a rustic atmosphere.
            2. The Harbor: a seafood restaurant with a view of the ocean.
            3. The Joint: a casual eatery with a diverse menu.
            """

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(
        self, restaurant: Literal["The Farm, The Harbor, The Joint"]
    ) -> Annotated[str, "Returns the specials from the menu."]:
        match restaurant:
            case "The Farm":
                return """
                    Special Entree: T-bone steak
                    Special Salad: Caesar Salad
                    Special Drink: Old Fashioned
                    """
            case "The Harbor":
                return """
                    Special Soup: Lobster Bisque
                    Special Salad: Cobb Salad
                    Special Drink: Mai Tai
                    """
            case "The Joint":
                return """
                    Special Burger: Avocado and Jalapeno Burger
                    Special Salad: Greek Salad
                    Special Drink: Milkshake Strawberry
                    """
            case _:
                return "No specials available for this restaurant."

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self,
        restaurant: Literal["The Farm, The Harbor, The Joint"],
        menu_item: Annotated[str, "The name of the menu item."],
    ) -> Annotated[str, "Returns the price of the menu item."]:
        match restaurant:
            case "The Farm":
                return "$9.99"
            case "The Harbor":
                return "$12.99"
            case "The Joint":
                return "$8.99"
            case _:
                return "No price available for this restaurant."


async def run(transport: Literal["sse", "stdio"] = "stdio", port: int | None = None) -> None:
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Host",
        instructions="Answer questions about the menu for different restaurants, use the list_restaurants function "
        "to get the list of restaurants.",
        plugins=[RestaurantPlugin()],  # add the sample plugin to the agent
    )

    server = agent.as_mcp_server()

    if transport == "sse" and port is not None:
        import nest_asyncio
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (
                read_stream,
                write_stream,
            ):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )
        nest_asyncio.apply()
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)  # nosec
    elif transport == "stdio":
        from mcp.server.stdio import stdio_server

        async def handle_stdin(stdin: Any | None = None, stdout: Any | None = None) -> None:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        await handle_stdin()


if __name__ == "__main__":
    args = parse_arguments()
    anyio.run(run, args.transport, args.port)
