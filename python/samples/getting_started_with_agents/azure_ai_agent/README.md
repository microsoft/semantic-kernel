## Azure AI Agents

The following getting started samples show how to use Azure AI Agents with Semantic Kernel.

To set up the required resources, follow the "Quickstart: Create a new agent" guide [here](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure).

You will need to install the optional Semantic Kernel `azure` dependencies if you haven't already via:

```bash
pip install semantic-kernel
```

Before running an Azure AI Agent, modify your .env file to include:

```bash
AZURE_AI_AGENT_ENDPOINT = "<example-endpoint-string>"
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = "<example-deployment-name>"
AZURE_AI_AGENT_API_VERSION = "<example-api-version>"
```

The endpoint can be found listed as part of the Azure Foundry [portal](https://ai.azure.com) in the format of: `https://<resource>.services.ai.azure.com/api/projects/<project-name>`.

The .env should be placed in the root directory.

## Configuring the AI Project Client

Ensure that your Azure AI Agent resources are configured with at least a Basic or Standard SKU.

To begin, create the project client as follows:

```python
async with (
    DefaultAzureCredential() as creds,
    AzureAIAgent.create_client(credential=creds) as client,
):
    # Your operational code here
```

### Required Imports

The required imports for the `Azure AI Agent` include async libraries:

```python
from azure.identity.aio import DefaultAzureCredential
```

### Initializing the Agent

You can pass in an endpoint, along with an optional api-version, to create the client:

```python

ai_agent_settings = AzureAIAgentSettings()

async with (
    DefaultAzureCredential() as creds,
    AzureAIAgent.create_client(
        credential=creds,
        endpoint=ai_agent_settings.endpoint,
        api_version=ai_agent_settings.api_version,
    ) as client,
):
    # operational logic
```

### Creating an Agent Definition

Once the client is initialized, you can define the agent:

```python
# Create agent definition
agent_definition = await client.agents.create_agent(
    model=ai_agent_settings.model_deployment_name,
    name=AGENT_NAME,
    instructions=AGENT_INSTRUCTIONS,
)
```

Then, instantiate the `AzureAIAgent` with the `client` and `agent_definition`:

```python
# Create the AzureAI Agent
agent = AzureAIAgent(
    client=client,
    definition=agent_definition,
)
```

Now, you can create a thread, add chat messages to the agent, and invoke it with given inputs and optional parameters.

### Reusing an Agent Definition

In certain scenarios, you may prefer to reuse an existing agent definition rather than creating a new one. This can be done by calling `await client.agents.get_agent(...)` instead of `await client.agents.create_agent(...)`. 

For a practical example, refer to the [`step7_azure_ai_agent_retrieval`](./step7_azure_ai_agent_retrieval.py) sample.

## Requests and Rate Limits

### Managing API Request Frequency

Your default request limits may be low, affecting how often you can poll the status of a run. You have two options:

1. Adjust the `polling_options` of the `AzureAIAgent`

By default, the polling interval is 250 ms. You can slow it down to 1 second (or another preferred value) to reduce the number of API calls:

```python
# Required imports
from datetime import timedelta
from semantic_kernel.agents.run_polling_options import RunPollingOptions

# Configure the polling options as part of the `AzureAIAgent`
agent = AzureAIAgent(
    client=client,
    definition=agent_definition,
    polling_options=RunPollingOptions(run_polling_interval=timedelta(seconds=1)),
)
```

2. Increase Rate Limits in Azure AI Foundry

You can also adjust your deployment's Rate Limit (Tokens per minute), which impacts the Rate Limit (Requests per minute). This can be configured in Azure AI Foundry under your project's deployment settings for the "Connected Azure OpenAI Service Resource."
