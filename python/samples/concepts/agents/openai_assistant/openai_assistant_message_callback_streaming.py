# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.contents import AuthorRole, FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
This sample demonstrates how to create an AzureAssistantAgent/OpenAIAssistantAgent and use it with the 
streaming `invoke_stream()` method. The agent returns assistant messages as a stream of incremental chunks. 
In addition, you can specify an `on_intermediate_message` callback to receive fully-formed tool-related 
messages — such as function calls and their results — while the assistant response is still being streamed.

In this example, the agent is configured with a plugin that provides menu specials and item pricing.
As the user interacts with the agent, tool messages (like function calls) are emitted via the callback,
while assistant replies stream back incrementally through the main response loop.
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
async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Define the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
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

            first_chunk = True
            async for response in agent.invoke_stream(
                messages=user_input,
                thread=thread,
                on_intermediate_message=handle_streaming_intermediate_steps,
            ):
                thread = response.thread
                if first_chunk:
                    print(f"# {response.role}: ", end="", flush=True)
                    first_chunk = False
                print(response.content, end="", flush=True)
            print()
    finally:
        await thread.delete() if thread else None
        await client.beta.assistants.delete(assistant_id=agent.id)

    """
    Sample Output:

    # AuthorRole.USER: 'Hello'
    # AuthorRole.ASSISTANT: Hello! How can I help you with the menu today?
    # AuthorRole.USER: 'What is the special soup?'
    Function Call:> MenuPlugin-get_specials with arguments: {}
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    # AuthorRole.ASSISTANT: The special soup today is Clam Chowder. Would you like to know more about it or see other 
        specials?
    # AuthorRole.USER: 'What is the special drink?'
    # AuthorRole.ASSISTANT: The special drink is Chai Tea. Would you like more information about it or the other 
        specials?
    # AuthorRole.USER: 'How much is that?'
    Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Chai Tea"}
    Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # AuthorRole.ASSISTANT: The special drink, Chai Tea, is $9.99. Would you like to order one or have questions about 
        something else on the menu?
    # AuthorRole.USER: 'Thank you'
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions or need help with the menu, just let me 
        know. Enjoy your meal!
    """


if __name__ == "__main__":
    asyncio.run(main())
