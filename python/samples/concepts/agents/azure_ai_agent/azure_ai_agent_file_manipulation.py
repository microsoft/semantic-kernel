# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.projects.models import CodeInterpreterTool, FilePurpose
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create a simple,
Azure AI agent that uses the code interpreter tool to answer
a coding question.
"""


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

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

        # Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        user_inputs = [
            "Which segment had the most sales?",
            "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]

        try:
            for user_input in user_inputs:
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified user input
                async for response in agent.invoke(messages=user_input, thread=thread):
                    if response.role != AuthorRole.TOOL:
                        print(f"# Agent: {response}")
                        if len(response.items) > 0:
                            for item in response.items:
                                # Show Annotation Content if it exist
                                if isinstance(item, AnnotationContent):
                                    print(f"\n`{item.quote}` => {item.file_id}")
                                    response_content = await client.agents.get_file_content(file_id=item.file_id)
                                    content_bytes = bytearray()
                                    async for chunk in response_content:
                                        content_bytes.extend(chunk)
                                    tab_delimited_text = content_bytes.decode("utf-8")
                                    print(tab_delimited_text)
                    thread = response.thread
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
