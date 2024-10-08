# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

###################################################################
# The following sample demonstrates how to configure the auto     #
# function invocation filter with use of a ChatCompletionAgent.   #
###################################################################


# Define the agent name and instructions
HOST_NAME = "Host"
HOST_INSTRUCTIONS = "Answer questions about the menu."


# Define the auto function invocation filter that will be used by the kernel
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    # if we don't call next, it will skip this function, and go to the next one
    await next(context)
    if context.function.plugin_name == "menu":
        context.terminate = True


# Define a sample plugin for the sample
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


def _create_kernel_with_chat_completionand_filter(service_id: str) -> Kernel:
    """A helper function to create a kernel with a chat completion service and a filter."""
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auto_function_invocation_filter)
    kernel.add_plugin(plugin=MenuPlugin(), plugin_name="menu")
    return kernel


def _write_content(content: ChatMessageContent) -> None:
    """Write the content to the console."""
    last_item_type = type(content.items[-1]).__name__ if content.items else "(empty)"
    message_content = ""
    if isinstance(last_item_type, FunctionCallContent):
        message_content = f"tool request = {content.items[-1].function_name}"
    elif isinstance(last_item_type, FunctionResultContent):
        message_content = f"function result = {content.items[-1].result}"
    else:
        message_content = str(content.items[-1])
    print(f"[{last_item_type}] {content.role} : '{message_content}'")


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: ChatCompletionAgent, input: str, chat_history: ChatHistory) -> None:
    """Invoke the agent with the user input."""
    chat_history.add_user_message(input)
    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(chat_history):
        if not any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in content.items):
            chat_history.add_message(content)
        _write_content(content)


async def main():
    service_id = "agent"

    # Create the kernel used by the chat completion agent
    kernel = _create_kernel_with_chat_completionand_filter(service_id=service_id)

    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)

    # Configure the function choice behavior to auto invoke kernel functions
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create the agent
    agent = ChatCompletionAgent(
        service_id=service_id,
        kernel=kernel,
        name=HOST_NAME,
        instructions=HOST_INSTRUCTIONS,
        execution_settings=settings,
    )

    # Define the chat history
    chat = ChatHistory()

    # Respond to user input
    await invoke_agent(agent=agent, input="Hello", chat_history=chat)
    await invoke_agent(agent=agent, input="What is the special soup?", chat_history=chat)
    await invoke_agent(agent=agent, input="What is the special drink?", chat_history=chat)
    await invoke_agent(agent=agent, input="Thank you", chat_history=chat)

    print("================================")
    print("CHAT HISTORY")
    print("================================")

    # Print out the chat history to view the different types of messages
    for message in chat.messages:
        _write_content(message)


if __name__ == "__main__":
    asyncio.run(main())
