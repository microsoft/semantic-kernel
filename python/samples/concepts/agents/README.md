# Semantic Kernel: Agent concept examples

This project contains a step by step guide to get started with _Semantic Kernel Agents_ in Python.

## PyPI

- For the use of Chat Completion agents, the minimum allowed Semantic Kernel pypi version is 1.3.0.
- For the use of OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.4.0.
- For the use of Agent Group Chat, the minimum allowed Semantic kernel pypi version is 1.6.0.
- For the use of Streaming OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.11.0.
- For the use of AzureAI and Bedrock agents, the minimum allowed Semantic Kernel pypi version is 1.21.0.
- For the use of Crew.AI as a plugin, the minimum allowed Semantic Kernel pypi version is 1.21.1.
- For the use of OpenAI Responses agents, the minimum allowed Semantic Kernel pypi version is 1.27.0.

## Source

- [Semantic Kernel Agent Framework](../../../semantic_kernel/agents/)

## Examples

The concept agents examples are grouped by prefix:

Prefix|Description
---|---
autogen_conversable_agent| How to use [AutoGen 0.2 Conversable Agents](https://microsoft.github.io/autogen/0.2/docs/Getting-Started) within Semantic Kernel.
azure_ai_agent|How to use an [Azure AI Agent](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure) within Semantic Kernel.
chat_completion_agent|How to use Semantic Kernel Chat Completion agents that leverage AI Connector Chat Completion APIs.
bedrock|How to use [AWS Bedrock agents](https://aws.amazon.com/bedrock/agents/) in Semantic Kernel.
mixed_chat|How to combine different agent types.
openai_assistant|How to use [OpenAI Assistants](https://platform.openai.com/docs/assistants/overview) in Semantic Kernel.
openai_responses|How to use [OpenAI Responses](https://platform.openai.com/docs/api-reference/responses) in Semantic Kernel.

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key or token authentication
for your AI connector, the samples run without any extra command line arguments.

## Managing Conversation Threads with AgentThread

This section explains how to manage conversation context using the `AgentThread` base class. Each agent has its own thread implementation that preserves the context of a conversation. If you invoke an agent without specifying a thread, a new one is created automatically and returned as part of the `AgentItemResponse` object—which includes both the message (of type `ChatMessageContent`) and the thread (`AgentThread`). You also have the option to create a custom thread for a specific agent by providing a unique `thread_id`.

## Overview

**Automatic Thread Creation:**  
When an agent is invoked without a provided thread, it creates a new thread to manage the conversation context automatically.

**Manual Thread Management:**  
You can explicitly create a specific implementation for the desired `Agent` that derives from the base class `AgentThread`. You have the option to assign a `thread_id` to manage the conversation session. This is particularly useful in complex scenarios or multi-user environments.

## Code Example

Below is a sample code snippet demonstrating thread management:

```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

USER_INPUTS = [
    "Why is the sky blue?",
]

# 1. Create the agent by specifying the service
agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="Assistant",
    instructions="Answer the user's questions.",
)

# 2. Create a thread to hold the conversation
# If no thread is provided, a new thread will be
# created and returned with the initial response
thread = None

for user_input in USER_INPUTS:
    print(f"# User: {user_input}")
    # 3. Invoke the agent for a response
    response = await agent.get_response(
        message=user_input,
        thread=thread,
    )
    print(f"# {response.name}: {response}")
    thread = response.thread

# 4. Cleanup: Clear the thread
await thread.end() if thread else None

"""
Sample output:
# User: Hello, I am John Doe.
# Assistant: Hello, John Doe! How can I assist you today?
# User: What is your name?
# Assistant: I don't have a personal name like a human does, but you can call me Assistant.?
# User: What is my name?
# Assistant: You mentioned that your name is John Doe. How can I assist you further, John?
"""
```

## Detailed Explanation

**Thread Initialization:**  
The thread is initially set to `None`. If no thread is provided, the agent creates a new one and includes it in the response.

**Processing User Inputs:**  
A list of `user_inputs` simulates a conversation. For each input:
- The code prints the user's message.
- The agent is invoked using the `get_response` method, which returns the response asynchronously.

**Handling Responses:**  
- The thread is updated with each response to maintain the conversation context.

**Cleanup:**  
The code safely ends the thread if it exists.

By leveraging the `AgentThread`, you ensure that each conversation maintains its context seamlessly -- whether the thread is automatically created or manually managed with a custom `thread_id`. This approach is crucial for developing agents that deliver coherent and context-aware interactions.



