# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.filters import (
    AutoFunctionInvocationContext,
    FilterTypes,
)
from semantic_kernel.functions import FunctionResult, kernel_function
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. This sample demonstrates the basic steps to create an agent
and simulate a conversation with the agent.

This sample demonstrates how to create a filter that will be called for each
function call in the response. The filter can be used to modify the function
result or to terminate the function call. The filter can also be used to
log the function call or to perform any other action before or after the
function call.
"""


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


# Define a kernel instance so we can attach the filter to it
kernel = Kernel()


# Define a list to store intermediate steps
intermediate_steps: list[ChatMessageContent] = []


# Define a callback function to handle intermediate step content messages
async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    print("\nAuto function invocation filter")
    print(f"Function: {context.function.name}")

    # if we don't call next, it will skip this function, and go to the next one
    await next(context)
    """
    Note: to simply return the unaltered function results, uncomment the `context.terminate = True` line and
    comment out the lines starting with `result = context.function_result` through `context.terminate = True`.
    context.terminate = True
    For this sample, simply setting `context.terminate = True` will return the unaltered function result:
    
    Auto function invocation filter
    Function: get_specials
    # Assistant: MenuPlugin-get_specials - 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
    """
    result = context.function_result
    if "menu" in context.function.plugin_name.lower():
        print("Altering the Menu plugin function result...\n")
        context.function_result = FunctionResult(
            function=result.function,
            value="We are sold out, sorry!",
        )
        context.terminate = True


# Simulate a conversation with the agent
USER_INPUTS = ["What's the special food on the menu?", "What should I do then?"]


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Host",
            instructions="Answer the user's questions about the menu.",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            kernel=kernel,
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # Add the plugin to the agent
        )

        # 3. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. Invoke the agent with the specified message for response
                async for response in agent.invoke(
                    messages=user_input, thread=thread, on_intermediate_message=handle_intermediate_steps
                ):
                    # 5. Print the response
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread and agent
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

        """
        Sample Output:
        
        # User: What's the special food on the menu?

        Auto function invocation filter
        Function: get_specials
        Altering the Menu plugin function result...

        # Host: I'm sorry, but all the specials on the menu are currently sold out. If there's anything else you're 
            looking for, please let me know!
        # User: What should I do then?
        # Host: You might consider ordering from the regular menu items instead. If you need any recommendations or 
            information about specific items, such as prices or ingredients, feel free to ask!

        Intermediate Steps:
        Function Call:> MenuPlugin-get_specials with arguments: {}
        Function Result:> We are sold out, sorry! for function: MenuPlugin-get_specials
        AuthorRole.ASSISTANT: I'm sorry, but all the specials on the menu are currently sold out. If there's anything 
            else you're looking for, please let me know!
        AuthorRole.ASSISTANT: You might consider ordering from the regular menu items instead. If you need any 
            recommendations or information about specific items, such as prices or ingredients, feel free to ask!
        """


if __name__ == "__main__":
    asyncio.run(main())
