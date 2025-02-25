# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat working on
an uploaded file.
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "mixed_chat_files",
        "user-context.txt",
    )

    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # If desired, create using OpenAI resources
    # client, model = OpenAIAssistantAgent.setup_resources()

    # Load the text file as a FileObject
    with open(file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    code_interpreter_tool, code_interpreter_tool_resource = AzureAssistantAgent.configure_code_interpreter_tool(
        file_ids=file.id
    )

    definition = await client.beta.assistants.create(
        model=model,
        instructions="Create charts as requested without explanation.",
        name="ChartMaker",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_tool_resource,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    analyst_agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    service_id = "summary"
    summary_agent = ChatCompletionAgent(
        service_id=service_id,
        kernel=_create_kernel_with_chat_completion(service_id=service_id),
        instructions="Summarize the entire conversation for the user in natural language.",
        name="SummaryAgent",
    )

    # Create the AgentGroupChat object, which will manage the chat between the agents
    # We don't always need to specify the agents in the chat up front
    # As shown below, calling `chat.invoke(agent=<agent>)` will automatically add the
    # agent to the chat
    chat = AgentGroupChat()

    try:
        user_and_agent_inputs = (
            (
                "Create a tab delimited file report of the ordered (descending) frequency distribution of "
                "words in the file 'user-context.txt' for any words used more than once.",
                analyst_agent,
            ),
            (None, summary_agent),
        )

        for input, agent in user_and_agent_inputs:
            if input:
                await chat.add_chat_message(input)
                print(f"# {AuthorRole.USER}: '{input}'")

            async for content in chat.invoke(agent=agent):
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
                if len(content.items) > 0:
                    for item in content.items:
                        if (
                            isinstance(agent, AzureAssistantAgent)
                            and isinstance(item, AnnotationContent)
                            and item.file_id
                        ):
                            print(f"\n`{item.quote}` => {item.file_id}")
                            response_content = await agent.client.files.content(item.file_id)
                            print(response_content.text)
    finally:
        await client.files.delete(file_id=file.id)
        await client.beta.assistants.delete(analyst_agent.id)


if __name__ == "__main__":
    asyncio.run(main())
