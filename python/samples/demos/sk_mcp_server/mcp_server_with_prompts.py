# /// script # noqa: CPY001
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import logging
from typing import Any

import anyio
from mcp.server.stdio import stdio_server

from semantic_kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger = logging.getLogger(__name__)

"""
This sample demonstrates how to expose your Semantic Kernel instance as a MCP server.

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
"""


def run() -> None:
    """Run the MCP server with the release notes prompt template."""
    kernel = Kernel()
    prompt = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="release_notes",
            description="This creates release notes from a list of PRs messages.",
            template="""{{$messages}}
---
Group the following PRs into one of these buckets for release notes, keeping the same order: 

-New Features 
-Enhancements and Improvements
-Bug Fixes
-Python Package Updates 

Include the output in raw markdown.
""",
            input_variables=[
                InputVariable(
                    name="messages",
                    description="These are the PR messages, they are a single string with new lines.",
                    is_required=True,
                    json_schema='{ "type": "string"}',
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
