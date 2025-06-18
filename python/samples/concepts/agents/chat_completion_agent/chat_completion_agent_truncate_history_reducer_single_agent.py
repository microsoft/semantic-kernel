# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.agents import (
    ChatCompletionAgent,
)
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import (
    ChatHistoryTruncationReducer,
)

"""
The following sample demonstrates how to implement a truncation chat 
history reducer as part of the Semantic Kernel Agent Framework. For 
this sample, a single ChatCompletionAgent is used.
"""


# Initialize the logger for debugging and information messages
logger = logging.getLogger(__name__)


async def main():
    # Setup necessary parameters
    reducer_msg_count = 10
    reducer_threshold = 10

    # Create a truncation reducer
    history_truncation_reducer = ChatHistoryTruncationReducer(
        target_count=reducer_msg_count,
        threshold_count=reducer_threshold,
    )

    thread: ChatHistoryAgentThread = ChatHistoryAgentThread(chat_history=history_truncation_reducer)

    # Create our agent
    agent = ChatCompletionAgent(
        name="NumeroTranslator",
        instructions="Add one to the latest user number and spell it in Spanish without explanation.",
        service=AzureChatCompletion(),
    )

    # Number of messages to simulate
    message_count = 50
    for index in range(1, message_count + 1, 2):
        print(f"# User: '{index}'")

        # Get agent response and store it
        response = await agent.get_response(messages=str(index), thread=thread)
        thread = response.thread
        print(f"# Agent - {response.name}: '{response.content}'")

        # Attempt reduction
        is_reduced = await thread.reduce()
        if is_reduced:
            print(f"@ History reduced to {len(thread)} messages.")

        print(f"@ Message Count: {len(history_truncation_reducer.messages)}\n")


if __name__ == "__main__":
    asyncio.run(main())
