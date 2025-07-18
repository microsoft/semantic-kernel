# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.functions import KernelArguments

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Local Agent with two local MCP Servers.

It uses a Ollama Chat Completion to create a agent, so make sure to 
set the required environment variables for the Azure AI Foundry service:
- OLLAMA_CHAT_MODEL_ID
"""

USER_INPUTS = [
    "list the latest 10 issues that have the label: triage and python and are open",
    """generate release notes with this list:             
* Python: Add ChatCompletionAgent integration tests by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11430
* Python: Update Doc Gen demo based on latest agent invocation api pattern by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11426
* Python: Update Python min version in README by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11428
* Python: Fix `TypeError` when required is missing in MCP tool’s inputSchema by @KanchiShimono in https://github.com/microsoft/semantic-kernel/pull/11458
* Python: Update chromadb requirement from <0.7,>=0.5 to >=0.5,<1.1 in /python by @dependabot in https://github.com/microsoft/semantic-kernel/pull/11420
* Python: Bump google-cloud-aiplatform from 1.86.0 to 1.87.0 in /python by @dependabot in https://github.com/microsoft/semantic-kernel/pull/11423
* Python: Support Auto Function Invocation Filter for AzureAIAgent and OpenAIAssistantAgent by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11460
* Python: Improve agent integration tests by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11475
* Python: Allow Kernel Functions from Prompt for image and audio content by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11403
* Python: Introducing SK as a MCP Server by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11362
* Python: sample using GitHub MCP Server and Azure AI Agent by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11465
* Python: allow settings to be created directly by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11468
* Python: Bug fix for azure ai agent truncate strategy. Add sample. by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11503
* Python: small code improvements in code of call automation sample by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11477
* Added missing import asyncio to agent with plugin python by @sphenry in https://github.com/microsoft/semantic-kernel/pull/11472
* Python: version updated to 1.28.0 by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11504""",
]


async def main():
    # Load the MCP Servers as Plugins
    async with (
        MCPStdioPlugin(
            name="Github",
            description="Github Plugin",
            command="docker",
            args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")},
        ) as github_plugin,
        MCPStdioPlugin(
            name="ReleaseNotes",
            description="SK Release Notes Plugin",
            command="uv",
            args=[
                f"--directory={str(Path(os.path.dirname(__file__)).parent.parent.joinpath('demos', 'mcp_server'))}",
                "run",
                "mcp_server_with_prompts.py",
            ],
        ) as release_notes_plugin,
    ):
        # Create the agent
        agent = ChatCompletionAgent(
            # Using the OllamaChatCompletion service
            service=OllamaChatCompletion(),
            name="GithubAgent",
            instructions="You interact with the user to help them with the Microsoft semantic-kernel github project. "
            "You have dedicated tools for this, including one to write release notes, "
            "make sure to use that when needed. The repo is always semantic-kernel (aka SK) with owner Microsoft. "
            "and when doing lists, always return 5 items and sort descending by created or updated"
            "You are specialized in Python, so always include label, python, in addition to the other labels.",
            plugins=[github_plugin, release_notes_plugin],
            function_choice_behavior=FunctionChoiceBehavior.Auto(
                filters={
                    # exclude a bunch of functions because the local models have trouble with too many functions
                    "included_functions": [
                        "Github-list_issues",
                        "ReleaseNotes-release_notes_prompt",
                    ]
                }
            ),
        )
        print(f"Agent uses Ollama with the {agent.service.ai_model_id} model")

        # Create a thread to hold the conversation
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: ChatHistoryAgentThread | None = None
        for user_input in USER_INPUTS:
            print(f"# User: {user_input}", end="\n\n")
            first_chunk = True
            async for response in agent.invoke_stream(
                messages=user_input,
                thread=thread,
                arguments=KernelArguments(owner="microsoft", repo="semantic-kernel"),
            ):
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                print(response.content, end="", flush=True)
                thread = response.thread
            print()

        # Cleanup: Clear the thread
        await thread.delete() if thread else None


if __name__ == "__main__":
    asyncio.run(main())
