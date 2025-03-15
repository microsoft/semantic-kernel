# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.projects.models import CodeInterpreterTool, FilePurpose
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create a simple,
Azure AI agent that uses the code interpreter tool to answer
a coding question.
"""


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        csv_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
            "resources",
            "agent_assistant_file_manipulation",
            "sales.csv",
        )

        file = await client.agents.upload_file_and_poll(file_path=csv_file_path, purpose=FilePurpose.AGENTS)

        code_interpreter = CodeInterpreterTool(file_ids=[file.id])

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread
        thread = await client.agents.create_thread()

        user_inputs = [
            "Which segment had the most sales?",
            "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]

        try:
            for user_input in user_inputs:
                # Add the user input as a chat message
                await agent.add_chat_message(
                    thread_id=thread.id,
                    message=user_input,
                )
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified thread
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
                        if len(content.items) > 0:
                            for item in content.items:
                                if isinstance(item, AnnotationContent):
                                    print(f"\n`{item.quote}` => {item.file_id}")
                                    response_content = await client.agents.get_file_content(file_id=item.file_id)
                                    content_bytes = bytearray()
                                    async for chunk in response_content:
                                        content_bytes.extend(chunk)
                                    tab_delimited_text = content_bytes.decode("utf-8")
                                    print(tab_delimited_text)
        finally:
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
