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

The .env should be placed in the root directory.

### Configuring the AI Project Client

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