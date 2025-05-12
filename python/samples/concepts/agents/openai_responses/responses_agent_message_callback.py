# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents import AzureResponsesAgent
from semantic_kernel.contents import AuthorRole, FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI
Responses Agent using either Azure OpenAI or OpenAI. The 
Responses Agent allow for function calling, the use of file search and a
web search tool. Responses Agent Threads are used to manage the
conversation state, similar to a Semantic Kernel Chat History.
Additionally, the invoke configures a message callback 
to receive the conversation messages during invocation.
"""


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


# This callback function will be called for each intermediate message,
# which will allow one to handle FunctionCallContent and FunctionResultContent.
# If the callback is not provided, the agent will return the final response
# with no intermediate tool call steps.
async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = AzureResponsesAgent(
        ai_model_id=model,
        client=client,
        name="Host",
        instructions="Answer questions about the menu.",
        plugins=[MenuPlugin()],
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    user_inputs = ["Hello", "What is the special soup?", "What is the special drink?", "How much is that?", "Thank you"]

    try:
        for user_input in user_inputs:
            print(f"# {AuthorRole.USER}: '{user_input}'")
            async for response in agent.invoke(
                messages=user_input,
                thread=thread,
                on_intermediate_message=handle_intermediate_steps,
            ):
                thread = response.thread
                print(f"# {response.name}: {response.content}")
    finally:
        await thread.delete() if thread else None

    """
    Sample Output:

    # AuthorRole.USER: 'Hello'
    # Host: Hi there! How can I assist you with the menu today?
    # AuthorRole.USER: 'What is the special soup?'
    Function Call:> MenuPlugin-get_specials with arguments: {}
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    # Host: The special soup is Clam Chowder. Would you like to know more about any other specials?
    # AuthorRole.USER: 'What is the special drink?'
    # Host: The special drink is Chai Tea. Would you like any more information?
    # AuthorRole.USER: 'How much is that?'
    Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Chai Tea"}
    Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # Host: The Chai Tea is $9.99. Is there anything else you'd like to know?
    # AuthorRole.USER: 'Thank you'
    # Host: You're welcome! If you have any more questions, feel free to ask. Enjoy your day!
    """


if __name__ == "__main__":
    asyncio.run(main())
