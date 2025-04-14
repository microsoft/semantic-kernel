# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an Azure AI Agent
and use it with functions. In order to answer user questions, the
agent internally uses the functions. These internal steps are returned
to the user as part of the agent's response. Thus, the invoke method
configures a message callback to receive the agent's internal messages. 

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


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        AGENT_NAME = "Host"
        AGENT_INSTRUCTIONS = "Answer questions about the menu."

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # add the sample plugin to the agent
        )

        # Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        user_inputs = [
            "Hello",
            "What is the special soup?",
            "How much does that cost?",
            "Thank you",
        ]

        try:
            for user_input in user_inputs:
                print(f"# User: '{user_input}'")
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                    on_intermediate_message=handle_intermediate_steps,
                ):
                    print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

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
    # Agent: Hello! How can I assist you today?
    # User: 'What is the special soup?'
    # Agent: The special soup is Clam Chowder. Would you like to know more about the menu or anything else?
    # User: 'How much does that cost?'
    # Agent: The Clam Chowder costs $9.99. If you have any more questions or need further assistance, feel free to ask!
    # User: 'Thank you'
    # Agent: You're welcome! If you have any more questions in the future, don't hesitate to ask. Have a great day!
    #
    # Intermediate Steps:
    # AuthorRole.ASSISTANT: Hello! How can I assist you today?
    # Function Call:> MenuPlugin-get_specials with arguments: {}
    # Function Result:>
    #         Special Soup: Clam Chowder
    #         Special Salad: Cobb Salad
    #         Special Drink: Chai Tea
    #         for function: MenuPlugin-get_specials
    # AuthorRole.ASSISTANT: The special soup is Clam Chowder. Would you like to know more about the menu or anything
    #                       else?
    # Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Clam Chowder"}
    # Function Result:> $9.99 for function: MenuPlugin-get_item_price
    # AuthorRole.ASSISTANT: The Clam Chowder costs $9.99. If you have any more questions or need further assistance,
    #                       feel free to ask!
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions in the future, don't hesitate to ask.
    #                       Have a great day!


if __name__ == "__main__":
    asyncio.run(main())
