# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin

# set this lower or higher depending on your needs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
The following sample demonstrates how to use a MCP Server that requires sampling
to generate release notes from a list of issues.

It uses the OpenAI service to create a agent, so make sure to 
set the required environment variables for the Azure AI Foundry service:
- OPENAI_API_KEY
- OPENAI_CHAT_MODEL_ID
"""

PR_MESSAGES = """* Python: Add ChatCompletionAgent integration tests by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11430
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
* Python: version updated to 1.28.0 by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11504"""


async def main():
    # 1. Create the agent
    async with MCPStdioPlugin(
        name="ReleaseNotes",
        description="SK Release Notes Plugin",
        command="uv",
        args=[
            f"--directory={str(Path(os.path.dirname(__file__)).parent.parent.joinpath('demos', 'mcp_server'))}",
            "run",
            "mcp_server_with_sampling.py",
        ],
    ) as plugin:
        agent = ChatCompletionAgent(
            service=OpenAIChatCompletion(),
            name="IssueAgent",
            instructions="For the messages supplied, call the release_notes_prompt function to get the broader "
            "prompt, then call the run_prompt function to get the final output, return that without any other text."
            "Do not add any other text to the output, or rewrite the output from run_prompt.",
            plugins=[plugin],
        )

        print(f"# Task: {PR_MESSAGES}")
        # 3. Invoke the agent for a response
        response = await agent.get_response(messages=PR_MESSAGES)
        print(str(response))

        # 4. Cleanup: Clear the thread
        await response.thread.delete()

        """
# Task: * Python: Add ChatCompletionAgent integration tests by @moonbox3 in https://github.com/microsoft/semantic-kernel/pull/11430
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
* Python: version updated to 1.28.0 by @eavanvalkenburg in https://github.com/microsoft/semantic-kernel/pull/11504

Here’s a summary of the recent changes and contributions made to the Microsoft Semantic Kernel repository:

1. **Integration Tests**: 
   - Added integration tests for `ChatCompletionAgent` by @moonbox3 ([PR #11430](https://github.com/microsoft/semantic-kernel/pull/11430)).
   - Improved agent integration tests by @moonbox3 ([PR #11475](https://github.com/microsoft/semantic-kernel/pull/11475)).

2. **Documentation and Demos**: 
   - Updated the Doc Gen demo to align with the latest agent invocation API pattern by @moonbox3 ([PR #11426](https://github.com/microsoft/semantic-kernel/pull/11426)).
   - Small code improvements made in the code of the call automation sample by @eavanvalkenburg ([PR #11477](https://github.com/microsoft/semantic-kernel/pull/11477)).

3. **Version Updates**:
   - Updated the minimum Python version in the README by @moonbox3 ([PR #11428](https://github.com/microsoft/semantic-kernel/pull/11428)).
   - Updated `chromadb` requirement to allow versions >=0.5 and <1.1 by @dependabot ([PR #11420](https://github.com/microsoft/semantic-kernel/pull/11420)).
   - Bumped `google-cloud-aiplatform` from 1.86.0 to 1.87.0 by @dependabot ([PR #11423](https://github.com/microsoft/semantic-kernel/pull/11423)).
   - Version updated to 1.28.0 by @eavanvalkenburg ([PR #11504](https://github.com/microsoft/semantic-kernel/pull/11504)).

4. **Bug Fixes**:
   - Fixed a `TypeError` in the MCP tool’s input schema when the required field is missing by @KanchiShimono ([PR #11458](https://github.com/microsoft/semantic-kernel/pull/11458)).
   - Bug fix for Azure AI agent truncate strategy with an added sample by @moonbox3 ([PR #11503](https://github.com/microsoft/semantic-kernel/pull/11503)).
   - Added a missing import for `asyncio` in the agent with plugin Python by @sphenry ([PR #11472](https://github.com/microsoft/semantic-kernel/pull/11472)).
        """


if __name__ == "__main__":
    asyncio.run(main())
