# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import OpenAISettings
from semantic_kernel.contents import AuthorRole, FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI
Responses Agent using either Azure OpenAI or OpenAI. The 
Responses Agent allow for function calling, the use of file search and a
web search tool. Responses Agent Threads are used to manage the
conversation state, similar to a Semantic Kernel Chat History.
Additionally, the invoke_stream configures a message callback 
to receive the conversation messages during streaming invocation.
This sample also demonstrates the Responses Agent Streaming
capability and how to manage a Responses Agent chat history.
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
    # 1. Create the client using Azure OpenAI resources and configuration
    client = OpenAIResponsesAgent.create_client()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = OpenAIResponsesAgent(
        ai_model_id=OpenAISettings().chat_model_id,
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

            first_chunk = True
            async for response in agent.invoke_stream(
                messages=user_input,
                thread=thread,
                on_intermediate_message=handle_streaming_intermediate_steps,
            ):
                thread = response.thread
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                print(response.content, end="", flush=True)
            print()
    finally:
        await thread.delete() if thread else None

    """
    Sample Output:

    # AuthorRole.USER: 'Hello'
    # Host: Hello! How can I assist you with the menu today?
    # AuthorRole.USER: 'What is the special soup?'
    Function Call:> MenuPlugin-get_specials with arguments: {}
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    # Host: The special soup today is Clam Chowder. Would you like to know more about it or hear about other specials?
    # AuthorRole.USER: 'What is the special drink?'
    # Host: The special drink today is Chai Tea. Would you like more details or are you interested in ordering it?
    # AuthorRole.USER: 'How much is that?'
    Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Chai Tea"}
    Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # Host: The special drink, Chai Tea, is $9.99. Would you like to order one or need information on something else?
    # AuthorRole.USER: 'Thank you'
    # Host: You're welcome! If you have any more questions or need help with the menu, just let me know. Enjoy your day!
    """


if __name__ == "__main__":
    asyncio.run(main())
