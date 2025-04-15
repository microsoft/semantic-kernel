# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.connectors.mcp import MCPStdioPlugin

"""
The following sample demonstrates how to create a AzureAIAgent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server.

It uses the Azure AI Foundry Agent service to create a agent, so make sure to 
set the required environment variables for the Azure AI Foundry service:
- AZURE_AI_AGENT_PROJECT_CONNECTION_STRING
- AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
"""


async def main():
    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
        # 2. Create the MCP plugin
        MCPStdioPlugin(
            name="github",
            description="Github Plugin",
            command="docker",
            args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")},
        ) as github_plugin,
    ):
        # 3. Create the agent, with the MCP plugin and the thread
        agent = AzureAIAgent(
            client=client,
            definition=await client.agents.create_agent(
                model=AzureAIAgentSettings.create().model_deployment_name,
                name="GithubAgent",
                instructions="You are a microsoft/semantic-kernel Issue Triage Agent. "
                "You look at all issues that have the tag: 'triage' and 'python'."
                "When you find one that is untriaged, you will suggest a new assignee "
                "based on the issue description, look at recent closed PR's for issues in the same area. "
                "You will also suggest additional context if needed, like related issues or a bug fix. ",
            ),
            plugins=[github_plugin],  # add the sample plugin to the agent
        )
        thread: AzureAIAgentThread | None = None
        # 4. Print instructions and set the initial user input
        print("Starting Azure AI Agent with MCP Plugin sample...")
        print("Once the first prompt is answered, you can further ask questions, use `exit` to exit.")
        user_input = "Find the latest untriaged, unassigned issues and suggest new assignees."
        print(f"# User: {user_input}")
        try:
            while user_input.lower() != "exit":
                # 5. Invoke the agent for a response
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response} ")
                thread = response.thread
                # 6. Get a new user input
                user_input = input("# User: ")
        finally:
            # 7. Cleanup: Clear the thread
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.definition.id)

        """
        Sample output:
GitHub MCP Server running on stdio
Starting Azure AI Agent with MCP Plugin sample...
Once the first prompt is answered, you can further ask questions, use `exit` to exit.
# User: Find the latest untriaged, unassigned issues and suggest new assignees.
# GithubAgent: Here are the latest untriaged and unassigned issues that are tagged with Python:

1. **[Issue #11459](https://github.com/microsoft/semantic-kernel/issues/11459)** 
   - **Title:** Python: Bug: The provided example is incorrect
   - **Description:** There are apparent mistakes in the provided Python examples concerning shared and 
   non-shared stateful configurations.
   - **Assignee Suggestion:** Assign to **eavanvalkenburg** based on prior involvement with Python-related code and 
   recent PRs focusing on bug fixes.

2. **[Issue #11465](https://github.com/microsoft/semantic-kernel/issues/11465)** 
   - **Title:** Python: sample using GitHub MCP Server and Azure AI Agent
   - **Description:** This adds a sample demonstrating how to use MCP tools with the Azure AI Agent.
   - **Assignee Suggestion:** Assign to **eavanvalkenburg** who is associated with the issue.

### Summary of Suggested Assignees:
- **Issue #11459**: **eavanvalkenburg**
- **Issue #11465**: **eavanvalkenburg**

It seems that I cannot update the assignees directly due to authentication issues. You can use this information 
as you see fit to assign these issues. If you need further assistance or specific context for each issue, 
please let me know! 
        """


if __name__ == "__main__":
    asyncio.run(main())
