# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentGroupChat, AzureAssistantAgent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureOpenAISettings
from semantic_kernel.contents import AnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat working with
image content.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Get the code interpreter tool and resources
    code_interpreter_tool, code_interpreter_resources = AzureAssistantAgent.configure_code_interpreter_tool()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        name="Analyst",
        instructions="Create charts as requested without explanation",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_resources,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    analyst_agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    service_id = "summary"
    summary_agent = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion(service_id=service_id),
        instructions="Summarize the entire conversation for the user in natural language.",
        name="Summarizer",
    )

    # Create the AgentGroupChat object, which will manage the chat between the agents
    # We don't always need to specify the agents in the chat up front
    # As shown below, calling `chat.invoke(agent=<agent>)` will automatically add the
    # agent to the chat
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
                            isinstance(agent, AzureAssistantAgent)
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
