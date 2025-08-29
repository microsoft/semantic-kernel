# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an Azure AI Agent
and use it with streaming responses. The agent is configured to use
a plugin that provides a list of specials from the menu and the price
of the requested menu item. The thread message ID is also printed as each
message is processed.
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


async def on_intermediate_msg(msg: ChatMessageContent) -> None:
    """Callback for intermediate messages."""
    if msg.metadata.get("thread_message_id"):
        print(f"Intermediate msg for {msg.content} with thread message id: {msg.metadata['thread_message_id']}")


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds, endpoint=ai_agent_settings.endpoint) as client,
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
            last_thread_msg_id = None
            for user_input in user_inputs:
                print(f"# User: '{user_input}'")
                first_chunk = True
                async for response in agent.invoke_stream(
                    messages=user_input, thread=thread, on_intermediate_message=on_intermediate_msg
                ):
                    if first_chunk:
                        print(f"# {response.role}: ", end="", flush=True)
                        first_chunk = False
                    print(response.content, end="", flush=True)
                    # Print thread message id only once per message (on change)
                    if "thread_message_id" in response.content.metadata:
                        current_id = response.content.metadata["thread_message_id"]
                        if current_id != last_thread_msg_id:
                            print(f" (thread message id: {current_id})", end="", flush=True)
                            last_thread_msg_id = current_id
                    thread = response.thread
                print()
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:

        # User: 'Hello'
        # AuthorRole.ASSISTANT: Hello (thread message id: msg_n0WKbpn6Uycn4of7gB8epoB7)! How can I assist you with 
            the menu today?
        # User: 'What is the special soup?'
        # AuthorRole.ASSISTANT: The (thread message id: msg_lUBXSeTnSvOSJPjTh5B1jPok) special soup today is 
            Clam Chowder. Would you like to know more about it or anything else on the menu?
        # User: 'How much does that cost?'
        # AuthorRole.ASSISTANT: The (thread message id: msg_3onftkPwMceCDYEDRHdwZTUd) Clam Chowder costs $9.99. 
            Would you like to order it or need information about something else?
        # User: 'Thank you'
        # AuthorRole.ASSISTANT: You're (thread message id: msg_DxE4nDzNi8D3z7QciuBewJbe) welcome! 
            If you have any more questions or need assistance, feel free to ask. Enjoy your meal!
        """


if __name__ == "__main__":
    asyncio.run(main())
