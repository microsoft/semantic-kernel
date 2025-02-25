## OpenAI Assistant Agents

The following getting started samples show how to use OpenAI Assistant agents with Semantic Kernel.

### OpenAI Assistant Agents

OpenAI Assistant Agents are created in the following way:

```python
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent

# Create the client using OpenAI resources and configuration
client, model = OpenAIAssistantAgent.setup_resources()

# Create the assistant definition
definition = await client.beta.assistants.create(
    model=model,
    instructions="<instructions>",
    name="<name>",
)

agent = OpenAIAssistantAgent(
    client=client,
    definition=definition,
)
```

### Azure Assistant Agents

Azure Assistant Agents are currently in preview and require a `-preview` API version (minimum version: `2024-05-01-preview`). As new features are introduced, API versions will be updated accordingly. For the latest versioning details, please refer to the [Azure OpenAI API preview lifecycle](https://learn.microsoft.com/azure/ai-services/openai/api-version-deprecation).

To specify the correct API version, set the following environment variable (for example, in your `.env` file):

```bash
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
```

Alternatively, you can pass the `api_version` parameter when creating an `AzureAssistantAgent`:

```python
from semantic_kernel.agents.open_ai import AzureAssistantAgent

# Create the client using Azure OpenAI resources and configuration
client, model = AzureAssistantAgent.setup_resources()

# Create the assistant definition
definition = await client.beta.assistants.create(
    model=model,
    instructions="<instructions>",
    name="<name>",
)

agent = AzureAssistantAgent(
    client=client,
    definition=definition,
)
```