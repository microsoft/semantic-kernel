# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from typing import Annotated

from semantic_kernel.agents import (
    AzureAssistantAgent,
    BooleanResult,
    ChatCompletionAgent,
    GroupChatOrchestration,
    MessageResult,
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureOpenAISettings
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.functions import kernel_function

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat to work towards
the user's requirement. The ChatCompletionAgent uses a plugin
that is part of the agent group chat.
"""


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
You should always tie the conversation back to the food specials offered by the plugin.
"""
REVIEWER_DESCRIPTION = "An art director who has opinions about copywriting born of a love for David Ogilvy."

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""
COPYWRITER_DESCRIPTION = "A copywriter with ten years of experience and known for brevity and a dry humor."


class MenuPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"


class ApprovalRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    @override
    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Check if the group chat should terminate.

        Args:
            chat_history (ChatHistory): The chat history of the group chat.
        """
        result = await super().should_terminate(chat_history)
        if result.result:
            return result

        # Check if the last message from the reviewer contains "approved"
        last_message = chat_history[-1]
        if (
            last_message.role == AuthorRole.ASSISTANT
            and last_message.name == REVIEWER_NAME
            and "approved" in last_message.content.lower()
        ):
            return BooleanResult(result=True, reason="The reviewer approved the content.")

        return BooleanResult(result=False, reason="The group chat is not ready to terminate.")

    @override
    async def filter_results(self, chat_history: ChatHistory) -> MessageResult:
        """Filter the chat history to only include relevant messages."""
        last_writer_message = next(
            (msg for msg in reversed(chat_history) if msg.role == AuthorRole.ASSISTANT and msg.name == COPYWRITER_NAME),
            None,
        )
        if last_writer_message:
            return MessageResult(
                result=last_writer_message,
                reason="Returning the last message from the writer as the result.",
            )
        return MessageResult(
            result=None,
            reason="No relevant message found from the writer.",
        )


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"{message.name}: {message.content}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"Calling '{item.name}' with arguments '{item.arguments}'")
        if isinstance(item, FunctionResultContent):
            print(f"Result from '{item.name}' is '{item.result}'")


async def main():
    # Create the agent reviewer agent
    agent_reviewer = ChatCompletionAgent(
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
        description=REVIEWER_DESCRIPTION,
        service=AzureChatCompletion(),
        plugins=[MenuPlugin()],
    )

    # Create the agent writer agent
    client = AzureAssistantAgent.create_client()
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        name=COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
        description=COPYWRITER_DESCRIPTION,
    )
    agent_writer = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    try:
        group_chat_orchestration = GroupChatOrchestration(
            members=[agent_writer, agent_reviewer],
            # max_rounds is odd, so that the writer gets the last round
            manager=ApprovalRoundRobinGroupChatManager(max_rounds=10),
            agent_response_callback=agent_response_callback,
        )

        runtime = InProcessRuntime()
        runtime.start()
        orchestration_result = await group_chat_orchestration.invoke(
            task="Write copy based on the food specials.",
            runtime=runtime,
        )

        value = await orchestration_result.get()
        print(f"***** Result *****\n{value}")
    finally:
        # Delete the agent
        await agent_writer.client.beta.assistants.delete(agent_writer.id)
        await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
