# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    ChatHistoryAgentThread,
)
from semantic_kernel.connectors.mcp import MCPStdioPlugin

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server. 
The Chat Completion Service is passed directly via the ChatCompletionAgent constructor.
Additionally, the plugin is supplied via the constructor.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "What are the latest 5 python issues in Microsoft/semantic-kernel?",
    "Are there any untriaged python issues?",
    "What is the status of issue #10785?",
]


async def main():
    # 1. Create the agent
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        MCPStdioPlugin(
            name="github",
            description="Github Plugin",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
        ) as github_plugin,
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="GithubAgent",
            instructions="You are a agent helping users deal with Github Issues. "
            "Unless specified otherwise, all questions are about the Microsoft semantic-kernel project.",
        )
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[github_plugin],  # add the sample plugin to the agent
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
