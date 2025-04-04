# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Literal

from semantic_kernel import Kernel
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger = logging.getLogger(__name__)

kernel = Kernel()


@kernel_function()
def echo_function(message: str, extra: str = "") -> str:
    """Echo a message as a function"""
    return f"Function echo: {message} {extra}"


agent = ChatCompletionAgent(
    service=OpenAIChatCompletion(),
    name="Agent",
    instructions="Answer questions from the user.",
)

kernel.add_service(OpenAIChatCompletion(service_id="default"))
kernel.add_plugin(agent, "agent")
kernel.add_function("echo", echo_function, "echo_function")
kernel.add_function(
    plugin_name="prompt",
    function_name="prompt",
    prompt_template_config=PromptTemplateConfig(
        name="prompt",
        description="This is a prompt",
        template="Please repeat this: {{$param1}} and this: {{$param2}}",
        input_variables=[
            InputVariable(
                name="message",
                description="This is the message.",
                is_required=True,
            ),
            InputVariable(
                name="param2",
                description="This is param2",
                default="default",
                is_required=False,
            ),
        ],
    ),
)


def run(transport: Literal["sse", "stdio"] = "stdio", port: int | None = None) -> None:
    server = create_mcp_server_from_kernel(kernel, prompt_functions=["agent-Agent"], tool_functions=[])

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

        async def handle_stdin(stdin: Any, stdout: Any) -> None:
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())

        anyio.run(handle_stdin)


if __name__ == "__main__":
    run(transport="sse", port=8000)
