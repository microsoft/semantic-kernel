# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat working with
image content.
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIAssistantAgent.setup_resources()

    # If desired, create using OpenAI resources
    # client, model = OpenAIAssistantAgent.setup_resources()

    code_interpreter_tool, code_interpreter_resources = OpenAIAssistantAgent.configure_code_interpreter_tool()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="Analyst",
        instructions="Create charts as requested without explanation",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_resources,
    )

    # Create the OpenAIAssistantAgent instance
    analyst_agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    service_id = "summary"
    summary_agent = ChatCompletionAgent(
        service_id=service_id,
        kernel=_create_kernel_with_chat_completion(service_id=service_id),
        instructions="Summarize the entire conversation for the user in natural language.",
        name="Summarizer",
    )

    # Note: By default, `AgentGroupChat` does not terminate automatically.
    # However, setting the maximum iterations to 5 forces the chat to end after 5 iterations.
    chat = AgentGroupChat()

    try:
        user_and_agent_inputs = (
            (
                """
                Graph the percentage of storm events by state using a pie chart:

                    State, StormCount
                    TEXAS, 4701
                    KANSAS, 3166
                    IOWA, 2337
                    ILLINOIS, 2022
                    MISSOURI, 2016
                    GEORGIA, 1983
                    MINNESOTA, 1881
                    WISCONSIN, 1850
                    NEBRASKA, 1766
                    NEW YORK, 1750
                """.strip(),
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
                            isinstance(agent, OpenAIAssistantAgent)
                            and isinstance(item, AnnotationContent)
                            and item.file_id
                        ):
                            print(f"\n`{item.quote}` => {item.file_id}")
                            response_content = await agent.client.files.content(item.file_id)
                            print(response_content.text)
    finally:
        await client.beta.assistants.delete(analyst_agent.id)


if __name__ == "__main__":
    asyncio.run(main())
