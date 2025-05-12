# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.contents import AuthorRole, FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an Assistant Agent
using either OpenAI or Azure OpenAI resources and use it with functions.
In order to answer user questions, the agent internally uses the
functions. These internal steps are returned to the user as part of the
agent's response. Thus, the invoke method configures a message callback
to receive the agent's internal messages. 

The agent is configured to use a plugin that provides a list of
specials from the menu and the price of the requested menu item.
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
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Define the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="Host",
        instructions="Answer questions about the menu.",
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition and the defined plugin
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
        plugins=[MenuPlugin()],
    )

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    user_inputs = [
        "Hello",
        "What is the special soup?",
        "What is the special drink?",
        "How much is that?",
        "Thank you",
    ]

    try:
        for user_input in user_inputs:
            print(f"# {AuthorRole.USER}: '{user_input}'")
            async for response in agent.invoke(
                messages=user_input,
                thread=thread,
                on_intermediate_message=handle_intermediate_steps,
            ):
                print(f"# {response.role}: {response}")
                thread = response.thread
    finally:
        await thread.delete() if thread else None
        await client.beta.assistants.delete(assistant_id=agent.id)

    """
    Sample Output:

    # AuthorRole.USER: 'Hello'
    # AuthorRole.ASSISTANT: Hello! How can I assist you today?
    # AuthorRole.USER: 'What is the special soup?'
    Function Call:> MenuPlugin-get_specials with arguments: {}
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    # AuthorRole.ASSISTANT: The special soup is Clam Chowder. Would you like to know more about the specials or 
        anything else?
    # AuthorRole.USER: 'What is the special drink?'
    # AuthorRole.ASSISTANT: The special drink is Chai Tea. If you have any more questions, feel free to ask!
    # AuthorRole.USER: 'How much is that?'
    Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Chai Tea"}
    Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # AuthorRole.ASSISTANT: The Chai Tea is priced at $9.99. If there's anything else you'd like to know, 
        just let me know!
    # AuthorRole.USER: 'Thank you'
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions or need further assistance, feel free to 
        ask. Enjoy your day!
    """


if __name__ == "__main__":
    asyncio.run(main())
