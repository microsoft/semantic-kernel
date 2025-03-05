# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import TYPE_CHECKING

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI, a chat completion  #
# agent and have them participate in a group chat to work towards   #
# the user's requirement. It also demonstrates how the underlying   #
# agent reset method is used to clear the current state of the chat #
#####################################################################

INSTRUCTIONS = """
The user may either provide information or query on information previously provided. 
If the query does not correspond with information provided, inform the user that their query cannot be answered.
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    try:
        assistant_agent = await OpenAIAssistantAgent.create(
            service_id="copywriter",
            kernel=Kernel(),
            name=f"{OpenAIAssistantAgent.__name__}",
            instructions=INSTRUCTIONS,
        )

        chat_agent = ChatCompletionAgent(
            service_id="chat",
            kernel=_create_kernel_with_chat_completion("chat"),
            name=f"{ChatCompletionAgent.__name__}",
            instructions=INSTRUCTIONS,
        )

        chat = AgentGroupChat()

        async def invoke_agent(agent: "Agent", input: str | None = None):
            if input is not None:
                await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
                print(f"\n{AuthorRole.USER}: '{input}'")

            async for message in chat.invoke(agent=agent):
                if message.content is not None:
                    print(f"\n# {message.role} - {message.name or '*'}: '{message.content}'")

        await invoke_agent(agent=assistant_agent, input="What is my favorite color?")
        await invoke_agent(agent=chat_agent)

        await invoke_agent(agent=assistant_agent, input="I like green.")
        await invoke_agent(agent=chat_agent)

        await invoke_agent(agent=assistant_agent, input="What is my favorite color?")
        await invoke_agent(agent=chat_agent)

        print("\nResetting chat...")
        await chat.reset()

        await invoke_agent(agent=assistant_agent, input="What is my favorite color?")
        await invoke_agent(agent=chat_agent)
    finally:
        await chat.reset()
        await assistant_agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
