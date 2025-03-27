## OpenAI Assistant Agents

The following getting started samples show how to use OpenAI Assistant agents with Semantic Kernel.

## Assistants API Overview

The Assistants API is a robust solution from OpenAI that empowers developers to integrate powerful, purpose-built AI assistants into their applications. It streamlines the development process by handling conversation histories, managing threads, and providing seamless access to advanced tools.

### Key Features

- **Purpose-Built AI Assistants:**  
  Assistants are specialized AIs that leverage OpenAI’s models to interact with users, access files, maintain persistent threads, and call additional tools. This enables highly tailored and effective user interactions.

- **Simplified Conversation Management:**  
  The concept of a **thread** -- a dedicated conversation session between an assistant and a user -- ensures that message history is managed automatically. Threads optimize the conversation context by storing and truncating messages as needed.

- **Integrated Tool Access:**  
  The API provides built-in tools such as:
  - **Code Interpreter:** Allows the assistant to execute code, enhancing its ability to solve complex tasks.
  - **File Search:** Implements best practices for retrieving data from uploaded files, including advanced chunking and embedding techniques.

- **Enhanced Function Calling:**  
  With improved support for third-party tool integration, the Assistants API enables assistants to extend their capabilities beyond native functions.

For more detailed technical information, refer to the [Assistants API](https://platform.openai.com/docs/assistants/overview).

### Semantic Kernel OpenAI Assistant Agents

OpenAI Assistant Agents are created in the following way:

```python
from semantic_kernel.agents import OpenAIAssistantAgent

# Create the client using OpenAI resources and configuration
client, model = OpenAIAssistantAgent.setup_resources()

# Create the assistant definition
definition = await client.beta.assistants.create(
    model=model,
    instructions="<instructions>",
    name="<name>",
)

# Define the Semantic Kernel OpenAI Assistant Agent
agent = OpenAIAssistantAgent(
    client=client,
    definition=definition,
)

# Define a thread
thread = None

# Invoke the agent
async for content in agent.invoke(messages="user input", thread=thread):
    print(f"# {content.role}: {content.content}")
    # Grab the thread from the response to continue with the current context
    thread = response.thread
```

### Semantic Kernel Azure Assistant Agents

Azure Assistant Agents are currently in preview and require a `-preview` API version (minimum version: `2024-05-01-preview`). As new features are introduced, API versions will be updated accordingly. For the latest versioning details, please refer to the [Azure OpenAI API preview lifecycle](https://learn.microsoft.com/azure/ai-services/openai/api-version-deprecation).

To specify the correct API version, set the following environment variable (for example, in your `.env` file):

```bash
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
```

Alternatively, you can pass the `api_version` parameter when creating an `AzureAssistantAgent`:

```python
from semantic_kernel.agents import AzureAssistantAgent

# Create the client using Azure OpenAI resources and configuration
client, model = AzureAssistantAgent.setup_resources()

# Create the assistant definition
definition = await client.beta.assistants.create(
    model=model,
    instructions="<instructions>",
    name="<name>",
)

# Define the Semantic Kernel Azure OpenAI Assistant Agent
agent = AzureAssistantAgent(
    client=client,
    definition=definition,
)

# Define a thread
thread = None

# Invoke the agent
async for content in agent.invoke(messages="user input", thread=thread):
    print(f"# {content.role}: {content.content}")
    # Grab the thread from the response to continue with the current context
    thread = response.thread
```