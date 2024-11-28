# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI, a chat completion  #
# agent and have them participate in a group chat to work towards   #
# the user's requirement. The ChatCompletionAgent uses a plugin     #
# that is part of the agent group chat.                             #
#####################################################################


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
You should always tie the conversation back to the food specials offered by the plugin.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""


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


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    kernel.add_plugin(plugin=MenuPlugin(), plugin_name="menu")
    return kernel


async def main():
    try:
        kernel = _create_kernel_with_chat_completion("artdirector")
        settings = kernel.get_prompt_execution_settings_from_service_id(service_id="artdirector")
        # Configure the function choice behavior to auto invoke kernel functions
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        agent_reviewer = ChatCompletionAgent(
            service_id="artdirector",
            kernel=kernel,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
            execution_settings=settings,
        )

        agent_writer = await OpenAIAssistantAgent.create(
            service_id="copywriter",
            kernel=Kernel(),
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )

        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        input = "Write copy based on the food specials."

        await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
        print(f"# {AuthorRole.USER}: '{input}'")

        async for content in chat.invoke():
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

        print(f"# IS COMPLETE: {chat.is_complete}")
    finally:
        await agent_writer.delete()


if __name__ == "__main__":
    asyncio.run(main())
