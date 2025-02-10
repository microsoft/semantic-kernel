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

### Configuring the AI Project Client

Please make sure you have configured the proper resources to be able to run an Azure AI Agent.

This can be done in one of two ways:

```python
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

or 

```python
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

### Requests and Rate Limits

Please note that your default rate limits/requests per minute may be low depending on how often you want to poll on the status of the run. You have two options:

1. Adjust the `polling_options` on the `AzureAIAgent` to slow down the number of times you make a server request for the status of the run. The default polling interval is 250 ms. You may adjust this to run every 1 second (or other desired value):

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

2. Adjust your deployment's `Rate Limit (Tokens per minute)`, which in turn adjusts the allowed `Rate Limit (Requests per minute)`). This is done in the Azure AI Foundry under your project's deployment for your "Connected Azure OpenAI Service Resource."