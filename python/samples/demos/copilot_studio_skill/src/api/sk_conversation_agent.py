# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="ChatAgent",
    instructions="You invent jokes to have a fun conversation with the user.",
)
