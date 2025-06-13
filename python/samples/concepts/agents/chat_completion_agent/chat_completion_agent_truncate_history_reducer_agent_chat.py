# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistoryTruncationReducer

"""
The following sample demonstrates how to implement a chat history
reducer as part of the Semantic Kernel Agent Framework. For this sample, 
the ChatCompletionAgent with an AgentGroupChat is used. The Chat History
Reducer is a Truncation Reducer. View the README for more information on 
how to use the reducer and what each parameter does.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


# Initialize the logger for debugging and information messages
logger = logging.getLogger(__name__)


async def main():
    """
    Single-function approach that shows the same chat reducer behavior
    while preserving all original logic and code lines (now commented).
    """

    # Setup necessary parameters
    reducer_msg_count = 10
    reducer_threshold = 10

    # Create a truncation reducer and clear its history
    history_truncation_reducer = ChatHistoryTruncationReducer(
        target_count=reducer_msg_count, threshold_count=reducer_threshold
    )
    history_truncation_reducer.clear()

    # Create our agent
    agent = ChatCompletionAgent(
        name="NumeroTranslator",
        instructions="Add one to the latest user number and spell it in Spanish without explanation.",
        service=AzureChatCompletion(),
    )

    # Create a group chat using the reducer
    chat = AgentGroupChat(chat_history=history_truncation_reducer)

    # Simulate user messages
    message_count = 50  # Number of messages to simulate
    for index in range(1, message_count, 2):
        # Add user message to the chat
        await chat.add_chat_message(message=str(index))
        print(f"# User: '{index}'")

        # Attempt to reduce history
        is_reduced = await chat.reduce_history()
        if is_reduced:
            print(f"@ History reduced to {len(history_truncation_reducer.messages)} messages.")

        # Invoke the agent and display responses
        async for message in chat.invoke(agent):
            print(f"# {message.role} - {message.name or '*'}: '{message.content}'")

        # Retrieve messages
        msgs = []
        async for m in chat.get_chat_messages(agent):
            msgs.append(m)
        print(f"@ Message Count: {len(msgs)}\n")


if __name__ == "__main__":
    asyncio.run(main())
