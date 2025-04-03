# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.filters import AutoFunctionInvocationContext
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to configure the auto
function invocation filter while using a ChatCompletionAgent.
This allows the developer or user to view the function call content
and the function result content.
"""


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


def _create_kernel_with_chat_completionand_filter() -> Kernel:
    """A helper function to create a kernel with a chat completion service and a filter."""
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())
    kernel.add_filter("auto_function_invocation", auto_function_invocation_filter)
    kernel.add_plugin(plugin=MenuPlugin(), plugin_name="menu")
    return kernel


def _write_content(content: ChatMessageContent) -> None:
    """Write the content to the console based on the content type."""
    last_item_type = type(content.items[-1]).__name__ if content.items else "(empty)"
    message_content = ""
    if isinstance(last_item_type, FunctionCallContent):
        message_content = f"tool request = {content.items[-1].function_name}"
    elif isinstance(last_item_type, FunctionResultContent):
        message_content = f"function result = {content.items[-1].result}"
    else:
        message_content = str(content.items[-1])
    print(f"[{last_item_type}] {content.role} : '{message_content}'")


async def main():
    # 1. Create the agent with a kernel instance that contains
    # the auto function invocation filter and the AI service
    agent = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completionand_filter(),
        name="Host",
        instructions="Answer questions about the menu.",
    )

    # 2. Define the thread
    thread: ChatHistoryAgentThread = None

    user_inputs = [
        "Hello",
        "What is the special soup?",
        "What is the special drink?",
        "Thank you",
    ]

    for user_input in user_inputs:
        print(f"# User: '{user_input}'")
        # 3. Get the response from the agent
        response = await agent.get_response(messages=user_input, thread=thread)
        thread = response.thread
        _write_content(response)

    print("================================")
    print("CHAT HISTORY")
    print("================================")

    # 4. Print out the chat history to view the different types of messages
    async for message in thread.get_messages():
        _write_content(message)

    """
    Sample output:

    # AuthorRole.USER: 'Hello'
    [TextContent] AuthorRole.ASSISTANT : 'Hello! How can I assist you today?'
    # AuthorRole.USER: 'What is the special soup?'
    [FunctionResultContent] AuthorRole.TOOL : '
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            '
    # AuthorRole.USER: 'What is the special drink?'
    [TextContent] AuthorRole.ASSISTANT : 'The special drink is Chai Tea.'
    # AuthorRole.USER: 'Thank you'
    [TextContent] AuthorRole.ASSISTANT : 'You're welcome! If you have any more questions or need assistance with 
        anything else, feel free to ask!'
    ================================
    CHAT HISTORY
    ================================
    [TextContent] AuthorRole.USER : 'Hello'
    [TextContent] AuthorRole.ASSISTANT : 'Hello! How can I assist you today?'
    [TextContent] AuthorRole.USER : 'What is the special soup?'
    [FunctionCallContent] AuthorRole.ASSISTANT : 'menu-get_specials({})'
    [FunctionResultContent] AuthorRole.TOOL : '
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            '
    [TextContent] AuthorRole.USER : 'What is the special drink?'
    [TextContent] AuthorRole.ASSISTANT : 'The special drink is Chai Tea.'
    [TextContent] AuthorRole.USER : 'Thank you'
    [TextContent] AuthorRole.ASSISTANT : 'You're welcome! If you have any more questions or need assistance with 
        anything else, feel free to ask!'
    """


if __name__ == "__main__":
    asyncio.run(main())
