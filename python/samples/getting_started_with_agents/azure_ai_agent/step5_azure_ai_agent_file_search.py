# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.projects.models import FileSearchTool, OpenAIFile, VectorStore
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a simple, Azure AI agent that
uses a file search tool to answer user questions.
"""

# Simulate a conversation with the agent
USER_INPUTS = [
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Read and upload the file to the Azure AI agent service
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
        )
        file: OpenAIFile = await client.agents.upload_file_and_poll(file_path=pdf_file_path, purpose="assistants")
        vector_store: VectorStore = await client.agents.create_vector_store_and_poll(
            file_ids=[file.id], name="my_vectorstore"
        )

        # 2. Create file search tool with uploaded resources
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        # 3. Create an agent on the Azure AI agent service with the file search tool
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        # 4. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. Create a new thread on the Azure AI agent service
        thread = await client.agents.create_thread()

        try:
            for user_input in USER_INPUTS:
                # 6. Add the user input as a chat message
                await agent.add_chat_message(thread_id=thread.id, message=user_input)
                print(f"# User: '{user_input}'")
                # 7. Invoke the agent for the specified thread for response
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
        finally:
            # 8. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: 'Who is the youngest employee?'
        # Agent: The youngest employee is Teodor Britton, who is an accountant and was born on January 9, 1997...
        # User: 'Who works in sales?'
        """


if __name__ == "__main__":
    asyncio.run(main())
