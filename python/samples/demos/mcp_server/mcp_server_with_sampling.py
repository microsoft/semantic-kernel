# /// script # noqa: CPY001
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import logging
from typing import Annotated, Any

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.prompt_template import InputVariable, KernelPromptTemplate, PromptTemplateConfig

logger = logging.getLogger(__name__)

"""
This sample demonstrates how to expose your Semantic Kernel `kernel` instance as a MCP server, with the a function 
that uses sampling (see the docs: https://modelcontextprotocol.io/docs/concepts/sampling) to generate release notes.

To run this sample, set up your MCP host (like Claude Desktop or VSCode Github Copilot Agents)
with the following configuration:
```json
{
    "mcpServers": {
        "sk_release_notes": {
            "command": "uv",
            "args": [
                "--directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server",
                "run",
                "mcp_server_with_prompts.py"
            ],
        }
    }
}
```

Note: You might need to set the uv to it's full path.
"""

template = """{{$messages}}
---
Group the following PRs into one of these buckets for release notes, keeping the same order: 

-New Features 
-Enhancements and Improvements
-Bug Fixes
-Python Package Updates 

Include the output in raw markdown.
"""


@kernel_function(
    name="run_prompt",
    description="This run the prompts for a full set of release notes based on the PR messages given.",
)
async def sampling_function(
    messages: Annotated[str, "The list of PR messages, as a string with newlines"],
    temperature: float = 0.0,
    max_tokens: int = 1000,
    # The include_in_function_choices is set to False, so it won't be included in the function choices,
    # but it will get the server instance from the MCPPlugin that consumes this server.
    server: Annotated[Server | None, "The server session", {"include_in_function_choices": False}] = None,
) -> str:
    if not server:
        raise ValueError("Request context is required for sampling function.")
    sampling_response = await server.request_context.session.create_message(
        messages=[
            types.SamplingMessage(role="user", content=types.TextContent(type="text", text=messages)),
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        model_preferences=types.ModelPreferences(
            hints=[types.ModelHint(name="gpt-4o-mini")],
        ),
    )
    logger.info(f"Sampling response: {sampling_response}")
    return sampling_response.content.text


def run() -> None:
    """Run the MCP server with the release notes prompt template."""
    kernel = Kernel()
    kernel.add_function("release_notes", sampling_function)
    prompt = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="release_notes_prompt",
            description="This creates the prompts for a full set of release notes based on the PR messages given.",
            template=template,
            input_variables=[
                InputVariable(
                    name="messages",
                    description="These are the PR messages, they are a single string with new lines.",
                    is_required=True,
                    json_schema='{"type": "string"}',
                )
            ],
        )
    )

    server = kernel.as_mcp_server(server_name="sk_release_notes", prompts=[prompt])

    async def handle_stdin(stdin: Any | None = None, stdout: Any | None = None) -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    anyio.run(handle_stdin)


if __name__ == "__main__":
    run()
