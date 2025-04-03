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


intermediate_steps: list[ChatMessageContent] = []


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


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

    # Print the final chat history
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

    """
    Sample Output:

    # AuthorRole.USER: 'Hello'
    # Host: Hi there! How can I assist you with the menu today?
    # AuthorRole.USER: 'What is the special soup?'
    # Host: The special soup is Clam Chowder.
    # AuthorRole.USER: 'What is the special drink?'
    # Host: The special drink is Chai Tea.
    # AuthorRole.USER: 'How much is that?'
    # Host: The Chai Tea is $9.99. Would you like to know more about the menu?
    # AuthorRole.USER: 'Thank you'
    # Host: You're welcome! If you have any questions about the menu or need assistance, feel free to ask.

    Intermediate Steps:
    AuthorRole.ASSISTANT: Hi there! How can I assist you with the menu today?
    AuthorRole.ASSISTANT: 
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    AuthorRole.ASSISTANT: The special soup is Clam Chowder.
    AuthorRole.ASSISTANT: 
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    AuthorRole.ASSISTANT: The special drink is Chai Tea.
    AuthorRole.ASSISTANT: Could you please specify the menu item you are asking about?
    AuthorRole.ASSISTANT: You're welcome! If you have any questions about the menu or need assistance, feel free to ask.
    """


if __name__ == "__main__":
    asyncio.run(main())
