# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    ChatHistoryAgentThread,
)
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server. 
The Chat Completion Service is passed directly via the ChatCompletionAgent constructor.
Additionally, the plugin is supplied via the constructor.
"""


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
            instructions="You are a microsoft/semantic-kernel Issue Triage Agent. "
            "You look at all issues that have the tag: 'triage' and 'python'."
            "When you find one that is untriaged, you will suggest a new assignee "
            "based on the issue description, look at recent closed PR's for issues in the same area. "
            "You will also suggest additional context if needed, like related issues or a bug fix. ",
        )
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[github_plugin],  # add the sample plugin to the agent
        )
        print("Starting Azure AI Agent with MCP Plugin sample...")
        print("Once the first prompt is answered, you can further ask questions, use `exit` to exit.")
        # Initial user input
        # This is the first message that will be sent to the agent
        user_input = "Find the latest untriaged, unassigned issues and suggest new assignees."
        print(f"# User: {user_input}")
        # 2. Create a thread to hold the conversation
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: ChatHistoryAgentThread | None = None
        messages = []
        try:
            while user_input.lower() != "exit":
                # 3. Invoke the agent for a response
                messages.append(ChatMessageContent(role=AuthorRole.USER, content=user_input))
                response = await agent.get_response(messages=messages, thread=thread)
                print(f"# {response.name}: {response} ")
                thread = response.thread
                user_input = input("# User: ")
        finally:
            # 4. Cleanup: Clear the thread
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent_definition.id)

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
