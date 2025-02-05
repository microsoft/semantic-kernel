# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import FileSearchTool, OpenAIFile, VectorStore
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

###################################################################
# The following sample demonstrates how to create a simple,       #
# Azure AI agent that uses the code interpreter tool to answer    #
# a coding question.                                              #
###################################################################


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
        )

        file: OpenAIFile = await client.agents.upload_file_and_poll(file_path=pdf_file_path, purpose="assistants")

        vector_store: VectorStore = await client.agents.create_vector_store_and_poll(
            file_ids=[file.id], name="my_vectorstore"
        )

        # Create file search tool with resources followed by creating agent
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread
        thread = await client.agents.create_thread()

        user_inputs = [
            "Who is the youngest employee?",
            "Who works in sales?",
            "I have a customer request, who can help me?",
        ]

        try:
            for user_input in user_inputs:
                # Add the user input as a chat message
                await agent.add_chat_message(
                    thread_id=thread.id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
                )
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified thread
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
        finally:
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
