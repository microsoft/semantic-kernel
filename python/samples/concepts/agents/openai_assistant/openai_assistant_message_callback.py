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


intermediate_steps: list[ChatMessageContent] = []


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


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

    # Print the intermediate steps
    print("\nIntermediate Steps:")
    for msg in intermediate_steps:
        if any(isinstance(item, FunctionResultContent) for item in msg.items):
            for fr in msg.items:
                if isinstance(fr, FunctionResultContent):
                    print(f"Function Result:> {fr.result} for function: {fr.name}")
        elif any(isinstance(item, FunctionCallContent) for item in msg.items):
            for fcc in msg.items:
                if isinstance(fcc, FunctionCallContent):
                    print(f"Function Call:> {fcc.name} with arguments: {fcc.arguments}")
        else:
            print(f"{msg.role}: {msg.content}")

    # Sample output:
    # User: 'Hello'
    # AuthorRole.ASSISTANT: Hello! How can I assist you today?
    # User: 'What is the special soup?'
    # AuthorRole.ASSISTANT: The special soup is Clam Chowder. Would you like to know more about the menu or any
    #                       specific items?
    # User: 'How much does that cost?'
    # AuthorRole.ASSISTANT: The Clam Chowder costs $9.99. Would you like to explore anything else on the menu?
    # User: 'Thank you'
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions or need assistance in the future, feel
    #                       free to ask. Have a great day!
    #
    # Intermediate Steps:
    # AuthorRole.ASSISTANT: Hello! How can I assist you today?
    # Function Call:> MenuPlugin-get_specials with arguments: {}
    # Function Result:>
    #         Special Soup: Clam Chowder
    #         Special Salad: Cobb Salad
    #         Special Drink: Chai Tea
    #          for function: MenuPlugin-get_specials
    # Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Clam Chowder"}
    # Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions or need assistance in the future, feel
    #                       free to ask. Have a great day!


if __name__ == "__main__":
    asyncio.run(main())
