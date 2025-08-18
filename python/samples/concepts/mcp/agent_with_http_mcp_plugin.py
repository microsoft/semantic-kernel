# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server.

It uses the Azure OpenAI service to create a agent, so make sure to
set the required environment variables for the Azure AI Foundry service:
- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- Optionally: AZURE_OPENAI_API_KEY
If this is not set, it's also possible to pass AsyncTokenCredential to the service, e.g. AzureCliCredential.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "How do I make a Python chat completion request in Semantic Kernel using Azure OpenAI?",
]


async def main():
    # 1. Create the agent
    async with MCPStreamableHttpPlugin(
        name="LearnSite",
        description="Learn Docs Plugin",
        url="https://learn.microsoft.com/api/mcp",
    ) as learn_plugin:
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name="DocsAgent",
            instructions="Answer questions about the Microsoft's Semantic Kernel SDK.",
            plugins=[learn_plugin],
        )

        for user_input in USER_INPUTS:
            # 2. Create a thread to hold the conversation
            # If no thread is provided, a new thread will be
            # created and returned with the initial response
            thread: ChatHistoryAgentThread | None = None

            print(f"# User: {user_input}")
            # 3. Invoke the agent for a response
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response} ")
            thread = response.thread

            # 4. Cleanup: Clear the thread
            await thread.delete() if thread else None


"""
Sample output:

# User: How do I make a Python chat completion request in Semantic Kernel using Azure OpenAI?
# DocsAgent: To make a **Python chat completion request in Semantic Kernel using Azure OpenAI**, follow these steps:

---

### 1. Install Semantic Kernel

```bash
pip install semantic-kernel
```

---

### 2. Import Necessary Libraries

```python
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
```

---

### 3. Initialize the Kernel and Add Azure OpenAI Service

```python
# Initialize the kernel
kernel = sk.Kernel()

# Set your Azure OpenAI details
deployment_name = "your-chat-deployment"
endpoint = "https://your-resource-name.openai.azure.com/"
api_key = "your-azure-openai-api-key"

# Add Azure Chat Completion service
kernel.add_chat_service(
    "azure_chat",
    AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
    ),
)
```

---

### 4. Create a Chat History and Send a Request

```python
# Create an initial chat history
history = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What can you do?"},
]

# Get chat completion
result = kernel.chat.complete(
    chat_history=history,
    max_tokens=100,
    temperature=0.7,
    top_p=0.95,
)

print(result)
```

---

## Example Summary

This makes a chat completion request to Azure OpenAI through Semantic Kernel in Python. You can add more user/assistant 
turns to `history`.
"""


if __name__ == "__main__":
    asyncio.run(main())
