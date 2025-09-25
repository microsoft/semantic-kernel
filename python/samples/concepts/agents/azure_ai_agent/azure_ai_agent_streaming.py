# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
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
                    messages=user_input,
                    thread=thread,
                ):
                    if first_chunk:
                        print(f"# {response.role}: ", end="", flush=True)
                        # Show the thread message id before the first text chunk
                        if "thread_message_id" in response.content.metadata:
                            current_id = response.content.metadata["thread_message_id"]
                            if current_id != last_thread_msg_id:
                                print(f"(thread message id: {current_id}) ", end="", flush=True)
                                last_thread_msg_id = current_id
                        first_chunk = False
                    print(response.content, end="", flush=True)
                    thread = response.thread
                print()
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:

        # User: 'Hello'
        # AuthorRole.ASSISTANT: (thread message id: msg_HZ2h4Wzbj7GEcnVCjnyEuYWT) Hello! How can I assist you with 
            the menu today?
        # User: 'What is the special soup?'
        # AuthorRole.ASSISTANT: (thread message id: msg_TSjkJK6hHJojIkPvF6uUofHD) The special soup today is 
            Clam Chowder. Would you like to know more about it or anything else from the menu?
        # User: 'How much does that cost?'
        # AuthorRole.ASSISTANT: (thread message id: msg_liwTpBFrB9JpCM1oM9EXKiwq) The Clam Chowder costs $9.99. 
            Is there anything else you'd like to know?
        # User: 'Thank you'
        # AuthorRole.ASSISTANT: (thread message id: msg_K6lpR3gYIHethXq17T6gJcxi) You're welcome! 
            If you have any more questions or need assistance, feel free to ask. Enjoy your meal!
        """


if __name__ == "__main__":
    asyncio.run(main())
