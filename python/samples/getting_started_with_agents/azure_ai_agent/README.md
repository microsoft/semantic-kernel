## Azure AI Agents

The following getting started samples show how to use Azure AI Agents with Semantic Kernel.

To set up the required resources, follow the "Quickstart: Create a new agent" guide [here](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure).

You will need to install the optional Semantic Kernel `azure` dependencies if you haven't already via:

```bash
pip install semantic-kernel[azure]
```

Before running an Azure AI Agent, modify your .env file to include:

```bash
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING = "<example-connection-string>"
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = "<example-model-deployment-name>"
```

or

```bash
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = "<example-model-deployment-name>"
AZURE_AI_AGENT_ENDPOINT = "<example-endpoint>"
AZURE_AI_AGENT_SUBSCRIPTION_ID = "<example-subscription-id>"
AZURE_AI_AGENT_RESOURCE_GROUP_NAME = "<example-resource-group-name>"
AZURE_AI_AGENT_PROJECT_NAME = "<example-project-name>"
```

The project connection string is of the following format: `<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<ProjectName>`. See [here](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure#configure-and-run-an-agent) for information on obtaining the values to populate the connection string.

The .env should be placed in the root directory.

## Configuring the AI Project Client

Ensure that your Azure AI Agent resources are properly configured with at least a Basic or Standard SKU.

### Required Imports

The required imports for the `Azure AI Agent` include async libraries:

```python
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
```

### Initializing the Agent

You can create an `AIProjectClient` using a connection string:

```python
async def main():
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
    # code
```

Or by explicitly specifying the endpoint and credentials:

```python
async def main():
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient(
            credential=creds,
            endpoint=ai_agent_settings.endpoint,
            subscription_id=ai_agent_settings.subscription_id,
            resource_group_name=ai_agent_settings.resource_group_name,
            project_name=ai_agent_settings.project_name
        ) as client,
    ):
    # code
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

## Requests and Rate Limits

### Managing API Request Frequency

Your default request limits may be low, affecting how often you can poll the status of a run. You have two options:

1. Adjust the `polling_options` of the `AzureAIAgent`

By default, the polling interval is 250 ms. You can slow it down to 1 second (or another preferred value) to reduce the number of API calls:

```python
# Required imports
from datetime import timedelta
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions

# Configure the polling options as part of the `AzureAIAgent`
agent = AzureAIAgent(
    client=client,
    definition=agent_definition,
    polling_options=RunPollingOptions(run_polling_interval=timedelta(seconds=1)),
)
```

2. Increase Rate Limits in Azure AI Foundry

You can also adjust your deployment's Rate Limit (Tokens per minute), which impacts the Rate Limit (Requests per minute). This can be configured in Azure AI Foundry under your project's deployment settings for the "Connected Azure OpenAI Service Resource."