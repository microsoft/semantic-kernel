# /// script # noqa: CPY001
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import argparse
import logging
from typing import Any, Literal

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger = logging.getLogger(__name__)

"""
This sample demonstrates how to expose your Semantic Kernel `kernel` instance as a MCP server.

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
                "sk_mcp_server.py"
            ],
            "env": {
                "OPENAI_API_KEY": "<your_openai_api_key>",
                "OPENAI_CHAT_MODEL_ID": "gpt-4o-mini"
            }
        }
    }
}
```

Note: You might need to set the uv to its full path.

Alternatively, you can run this as a SSE server, by setting the same environment variables as above, 
and running the following command:
```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server \
run sk_mcp_server.py --transport sse --port 8000
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


def run(transport: Literal["sse", "stdio"] = "stdio", port: int | None = None) -> None:
    kernel = Kernel()

    @kernel_function()
    def echo_function(message: str, extra: str = "") -> str:
        """Echo a message as a function"""
        return f"Function echo: {message} {extra}"

    kernel.add_service(OpenAIChatCompletion(service_id="default"))
    kernel.add_function("echo", echo_function, "echo_function")
    kernel.add_function(
        plugin_name="prompt",
        function_name="prompt",
        prompt_template_config=PromptTemplateConfig(
            name="prompt",
            description="This is a prompt",
            template="Please repeat this: {{$message}} and this: {{$extra}}",
            input_variables=[
                InputVariable(
                    name="message",
                    description="This is the message.",
                    is_required=True,
                    json_schema='{ "type": "string", "description": "This is the message."}',
                ),
                InputVariable(
                    name="extra",
                    description="This is extra.",
                    default="default",
                    is_required=False,
                    json_schema='{ "type": "string", "description": "This is the message."}',
                ),
            ],
        ),
    )
    server = kernel.as_mcp_server(server_name="sk")

    if transport == "sse" and port is not None:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)  # nosec
    elif transport == "stdio":
        import anyio
        from mcp.server.stdio import stdio_server

        async def handle_stdin(stdin: Any | None = None, stdout: Any | None = None) -> None:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        anyio.run(handle_stdin)


if __name__ == "__main__":
    args = parse_arguments()
    run(transport=args.transport, port=args.port)
