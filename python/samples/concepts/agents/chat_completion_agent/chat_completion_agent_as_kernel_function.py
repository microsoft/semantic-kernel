# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FunctionInvocationContext

"""
Todo
"""


# Define the auto function invocation filter that will be used by the kernel
async def function_invocation_filter(context: FunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    if "messages" not in context.arguments:
        await next(context)
        return
    print(f"    Agent {context.function.name} called with messages: {context.arguments['messages']}")
    await next(context)
    print(f"    Response from agent {context.function.name}: {context.result.value}")


# Create and configure the kernel.
kernel = Kernel()
kernel.add_filter("function_invocation", function_invocation_filter)

english_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="EnglishAgent",
    instructions="Your job is to help fulfill the user's request in English.",
)

spanish_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="SpanishAgent",
    instructions="Your job is to help fulfill the user's request in Spanish.",
)

french_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="FrenchAgent",
    instructions="Your job is to help fulfill the user's request in French.",
)

router_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    kernel=kernel,
    name="Router",
    instructions="This agent routes requests to the appropriate agent,",
    plugins=[english_agent, spanish_agent, french_agent],
)

thread: ChatHistoryAgentThread = None


async def chat() -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    response = await router_agent.get_response(
        messages=user_input,
        thread=thread,
    )

    if response:
        print(f"Agent :> {response}")

    return True


"""
Todo
"""


async def main() -> None:
    print(
        "Welcome to the chat bot!\n"
        "  Type 'exit' to exit.\n"
        "  Try to get some copy written by the copy writer, make sure to ask it is reviewed.)."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
