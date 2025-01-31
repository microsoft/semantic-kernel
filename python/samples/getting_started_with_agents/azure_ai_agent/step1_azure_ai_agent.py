# # Copyright (c) Microsoft. All rights reserved.

# import asyncio
# from typing import TYPE_CHECKING, Annotated

# from semantic_kernel import Kernel
# from semantic_kernel.agents import ChatCompletionAgent
# from semantic_kernel.connectors.ai import FunctionChoiceBehavior
# from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
# from semantic_kernel.contents import ChatHistory
# from semantic_kernel.contents.function_call_content import FunctionCallContent
# from semantic_kernel.contents.function_result_content import FunctionResultContent
# from semantic_kernel.functions import KernelArguments, kernel_function

# if TYPE_CHECKING:
#     pass


# ###################################################################
# # The following sample demonstrates how to create a simple,       #
# # non-group agent that utilizes plugins defined as part of        #
# # the Kernel.                                                     #
# ###################################################################


# # Define a sample plugin for the sample
# class MenuPlugin:
#     """A sample Menu Plugin used for the concept sample."""

#     @kernel_function(description="Provides a list of specials from the menu.")
#     def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
#         return """
#         Special Soup: Clam Chowder
#         Special Salad: Cobb Salad
#         Special Drink: Chai Tea
#         """

#     @kernel_function(description="Provides the price of the requested menu item.")
#     def get_item_price(
#         self, menu_item: Annotated[str, "The name of the menu item."]
#     ) -> Annotated[str, "Returns the price of the menu item."]:
#         return "$9.99"


# # Create the instance of the Kernel
# kernel = Kernel()
# kernel.add_plugin(MenuPlugin(), plugin_name="menu")

# service_id = "agent"
# kernel.add_service(AzureChatCompletion(service_id=service_id))

# settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
# # Configure the function choice behavior to auto invoke kernel functions
# settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

# # Define the agent name and instructions
# AGENT_NAME = "Host"
# AGENT_INSTRUCTIONS = "Answer questions about the menu."
# # Create the agent
# agent = AzureAIAgent(
#     service_id=service_id,
#     kernel=kernel,
#     name=AGENT_NAME,
#     instructions=AGENT_INSTRUCTIONS,
#     arguments=KernelArguments(settings=settings),
# )


# async def main():
#     # Define the chat history
#     chat_history = ChatHistory()

#     # Respond to user input
#     user_inputs = [
#         "Hello",
#         "What is the special soup?",
#         "What does that cost?",
#         "Thank you",
#     ]

#     for user_input in user_inputs:
#         # Add the user input to the chat history
#         chat_history.add_user_message(user_input)
#         print(f"# User: '{user_input}'")

#         agent_name: str | None = None
#         print("# Assistant - ", end="")
#         async for content in agent.invoke_stream(chat_history):
#             if not agent_name:
#                 agent_name = content.name
#                 print(f"{agent_name}: '", end="")
#             if (
#                 not any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in content.items)
#                 and content.content.strip()
#             ):
#                 print(f"{content.content}", end="", flush=True)
#         print("'")


# if __name__ == "__main__":
#     asyncio.run(main())

# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations to create messages with file search attachments from
    the Azure Agents service using a asynchronous client.

USAGE:
    python sample_agents_with_file_search_attachment_async.py

    Before running the sample:

    pip install azure-ai-projects azure-identity aiohttp

    Set this environment variables with your own values:
    PROJECT_CONNECTION_STRING - the Azure AI Project connection string, as found in your AI Foundry project.
"""

import asyncio
from typing import Annotated

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_decorator import kernel_function


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
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as project_client,
    ):
        AGENT_NAME = "Host"
        AGENT_INSTRUCTIONS = "Answer questions about the menu."

        # Create agent
        agent_model = await project_client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
        )

        agent = AzureAIAgent(
            client=project_client,
            agent=agent_model,
        )

        agent.kernel.add_plugin(MenuPlugin(), plugin_name="menu")

        thread = await project_client.agents.create_thread()

        user_inputs = [
            "Hello",
            "What is the special soup?",
            "What does that cost?",
            "Thank you",
        ]

        user_inputs = ["Hello", "What is the special soup?", "What is the special drink?", "Thank you"]
        try:
            for user_input in user_inputs:
                await agent.add_chat_message(
                    thread_id=thread.id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
                )
                print(f"# User: '{user_input}'")
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")

        finally:
            await agent.delete_thread(thread.id)
            await agent.delete()

        message = await project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="What feature does Smart Eyewear offer?",
        )
        print(f"Created message, message ID: {message.id}")

        run = await project_client.agents.create_and_process_run(
            thread_id=thread.id, assistant_id=agent.id, sleep_interval=4
        )
        print(f"Created run, run ID: {run.id}")

        print(f"Run completed with status: {run.status}")

        await project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

        messages = await project_client.agents.list_messages(thread_id=thread.id)
        print(f"Messages: {messages}")


if __name__ == "__main__":
    asyncio.run(main())
