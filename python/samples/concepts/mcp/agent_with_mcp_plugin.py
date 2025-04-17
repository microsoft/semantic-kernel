# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server. 

It uses the Azure OpenAI service to create a agent, so make sure to 
set the required environment variables for the Azure AI Foundry service:
- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- Optionally: AZURE_OPENAI_API_KEY 
If this is not set, it will try to use DefaultAzureCredential.

"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "What are the latest 5 python issues in Microsoft/semantic-kernel?",
    "Are there any untriaged python issues?",
    "What is the status of issue #10785?",
]


async def main():
    # 1. Create the agent
    async with MCPStdioPlugin(
        name="Github",
        description="Github Plugin",
        command="docker",
        args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")},
    ) as github_plugin:
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name="IssueAgent",
            instructions="Answer questions about the Microsoft semantic-kernel github project.",
            plugins=[github_plugin],
        )

        for user_input in USER_INPUTS:
            # 2. Create a thread to hold the conversation
            # If no thread is provided, a new thread will be
            # created and returned with the initial response
            thread: ChatHistoryAgentThread | None = None

            print(f"# User: {user_input}")
            # 3. Invoke the agent for a response
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response} ")
            thread = response.thread

            # 4. Cleanup: Clear the thread
            await thread.delete() if thread else None

        """
        Sample output:
GitHub MCP Server running on stdio
# User: What are the latest 5 python issues in Microsoft/semantic-kernel?
# IssueAgent: Here are the latest 5 Python issues in the 
[Microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) repository:

1. **[Issue #11358](https://github.com/microsoft/semantic-kernel/pull/11358)**  
   **Title:** Python: Bump Python version to 1.27.0 for a release.  
   **Created by:** [moonbox3](https://github.com/moonbox3)  
   **Created at:** April 3, 2025  
   **State:** Open  
   **Comments:** 1  
   **Description:** Bump Python version to 1.27.0 for a release.

2. **[Issue #11357](https://github.com/microsoft/semantic-kernel/pull/11357)**  
   **Title:** .Net: Version 1.45.0  
   **Created by:** [markwallace-microsoft](https://github.com/markwallace-microsoft)  
   **Created at:** April 3, 2025  
   **State:** Open  
   **Comments:** 0  
   **Description:** Version bump for release 1.45.0.

3. **[Issue #11356](https://github.com/microsoft/semantic-kernel/pull/11356)**  
   **Title:** .Net: Fix bug in sqlite filter logic  
   **Created by:** [westey-m](https://github.com/westey-m)  
   **Created at:** April 3, 2025  
   **State:** Open  
   **Comments:** 0  
   **Description:** Fix bug in sqlite filter logic.

4. **[Issue #11355](https://github.com/microsoft/semantic-kernel/issues/11355)**  
   **Title:** .Net: [MEVD] Validate that the collection generic key parameter corresponds to the model  
   **Created by:** [roji](https://github.com/roji)  
   **Created at:** April 3, 2025  
   **State:** Open  
   **Comments:** 0  
   **Description:** We currently have validation for the TKey generic type parameter passed to the collection type, 
   and we have validation for the key property type on the model.

5. **[Issue #11354](https://github.com/microsoft/semantic-kernel/issues/11354)**  
   **Title:** .Net: How to add custom JsonSerializer on a builder level  
   **Created by:** [PawelStadnicki](https://github.com/PawelStadnicki)  
   **Created at:** April 3, 2025  
   **State:** Open  
   **Comments:** 0  
   **Description:** Inquiry about adding a custom JsonSerializer for handling F# types within the SDK.

If you need more details about a specific issue, let me know! 
# User: Are there any untriaged python issues?
# IssueAgent: There are no untriaged Python issues in the Microsoft semantic-kernel repository. 
# User: What is the status of issue #10785?
# IssueAgent: The status of issue #10785 in the Microsoft Semantic Kernel repository is **open**. 

- **Title**: Port dotnet feature: Create MCP Sample
- **Created at**: March 4, 2025
- **Comments**: 0
- **Labels**: python 

You can view the issue [here](https://github.com/microsoft/semantic-kernel/issues/10785). 
        """


if __name__ == "__main__":
    asyncio.run(main())
