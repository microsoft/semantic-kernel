# Agent hosting

This folder contains a set of Aspire projects that demonstrate how to host a chat completion agent on Azure as a containerized service.

## Getting started

### Initialize the project

1. Open a terminal and navigate to the `AgentFrameworkWithAspire` directory.
2. Initialize the project by running the `azd init` command. **azd** will inspect the directory structure and determine the type of the app.
3. Select the `Use code in the current directory` option when **azd** prompts you with two app initialization options.
4. Select the `Confirm and continue initializing my app` option to confirm that **azd** found the correct `ChatWithAgent.AppHost` project.
5. Enter an environment name which is used to name provisioned resources.

### Deploy and provision the agent

1. Authenticate with Azure by running the `az login` command.
2. Provision all required resources and deploy the app to Azure by running the `azd up` command.
3. Select the subscription and location of the resources where the app will be deployed when prompted.
4. Provide required connection strings when prompted. More information on connection strings can be found in the [Connection strings](#connection-strings) section.
5. Copy the app endpoint URL from the output of the `azd up` command and paste it into a browser to see the app dashboard.
6. Click on the web frontend app link on the dashboard to navigate to the app.

Now you have the agent up and running on Azure. You can interact with the agent by typing messages in the chat window.
 
### Next steps

- [Enable RAG](#enable-rag)

### Additional information
- [Agent configuration](#agent-configuration)
- [Running agent locally](#running-agent-locally)
- [Clean up the resources](#clean-up-the-resources)
- [Deploy a .NET Aspire project(in-depth guide)](https://learn.microsoft.com/en-us/dotnet/aspire/deployment/azure/aca-deployment-azd-in-depth?tabs=windows)

## Agent configuration

The agent is defined by the `AgentDefinition.yaml` and `AgentWithRagDefinition.yaml` handlebar prompt templates, which are located in the `Resources` folder 
of the `ChatWithAgent.ApiService` project. The `AgentDefinition.yaml` template is used for a basic, non-RAG experience when RAG is not enabled.
Conversely, the `AgentWithRagDefinition.yaml` template is used when RAG is enabled.
   
To configure the agent, open one of the templates and modify the properties as needed. The following properties are available:

```yaml
name: <The name of the agent>
template: <The agent instructions>
template_format: handlebars
description: <The agent description>
execution_settings:
  default:
    temperature: 0
```

- `name`: This property defines the name of the agent. For example, `SupportBot` could be a name for an agent that provides customer support.
- `template`: This property gives specific instructions on how the agent should interact with users. An example could be, `Greet the user, ask how you can help, and provide solutions based on their questions.` This guides the agent on how to initiate conversations and respond to user inquiries.
- `description`: This property provides a brief description of the agent's role or purpose. For instance, `This bot assists users with support inquiries.` describes that the bot is intended to help users with their support-related questions.
- `temperature`: This property controls the randomness of the agent's responses. A higher temperature value results in more creative responses, while a lower value results in more predictable responses.

Other, model specific execution settings can be added to the `execution_settings` property along the `temperature` property to further customize the agent's behavior.
For example, the `stop_sequence` property can be added to specify a sequence of tokens that the agent should stop generating at.
List of available execution settings for a particular model can be found in the list of derived classes of the [PromptExecutionSettings](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.promptexecutionsettings?view=semantic-kernel-dotnet) class.

### Chat completion model configuration

The supported chat completion model configurations are located in the `AIServices` section of the `appsettings.json` file of the `ChatWithAgent.AppHost` project:

```json
{
  "AIServices": {
    "AzureOpenAIChat": {
      "DeploymentName": "gpt-4o-mini",
      "ModelName": "gpt-4o-mini",
      "ModelVersion": "2024-07-18",
      "SkuName": "S0",
      "SkuCapacity": 20
    },
    "OpenAIChat": {
      "ModelName": "gpt-4o-mini"
    }
  },
  "AIChatService": "AzureOpenAIChat"
}
```

#### Choose the chat completion model

Set the `AIChatService` property to the chat completion model to use. Choose one from the list of available models:
- `AzureOpenAIChat`: Azure OpenAI chat completion model.
- `OpenAIChat`: OpenAI chat completion model.

#### Configure the selected chat completion model

Depending on the selected service, configure the relevant properties:

`AzureOpenAIChat`:
- `DeploymentName`: The name of the deployment that hosts the chat completion model.
- `ModelName`: The name of the chat completion model.
- `ModelVersion`: The version of the chat completion model.
- `SkuName`: The SKU name of the chat completion model.
- `SkuCapacity`: The capacity of the chat completion model.
   
`OpenAIChat`:  
- `ModelName`: The name of the chat completion model.  

### Text embedding model configuration

The supported text embedding model configurations are located in the `AIServices` section of the `appsettings.json` file of the `ChatWithAgent.AppHost` project:

```json
{
  "AIServices": {
    "AzureOpenAIEmbeddings": {
      "DeploymentName": "text-embedding-3-small",
      "ModelName": "text-embedding-3-small",
      "ModelVersion": "2",
      "SkuName": "S0",
      "SkuCapacity": 20
    },
    "OpenAIEmbeddings": {
      "ModelName": "text-embedding-3-small"
    }
  },
  "Rag": {
    "AIEmbeddingService": "AzureOpenAIEmbeddings"
  }
}
```

#### Choose the text embedding service

Set the `AIEmbeddingService` property to the text embedding service you want to use. The available services are:
- `AzureOpenAIEmbeddings`: Azure OpenAI text embedding model.
- `OpenAIEmbeddings`: OpenAI text embedding model.

#### Configure the selected text embedding model

Depending on the selected service, configure the relevant properties:

`AzureOpenAIEmbeddings`:
- `DeploymentName`: The name of the deployment that hosts the text embedding model.
- `ModelName`: The name of the text embedding model.
- `ModelVersion`: The version of the text embedding model.
- `SkuName`: The SKU name of the text embedding model.`
- `SkuCapacity`: The capacity of the text embedding model.

`OpenAIEmbeddings`:
- `ModelName`: The name of the text embedding model.

### Vector store configuration

The supported vector store configurations are located in the `VectorStores` section of the `appsettings.json` file of the `ChatWithAgent.AppHost` project:

```json
{
  "VectorStores": {
    "AzureAISearch": {
    }
  },
  "Rag": {
    "VectorStoreType": "AzureAISearch"
  }
}
```

Currently, only the Azure AI Search vector store is supported so there is no need to change the configuration since it is already set to `AzureAISearch` by default.
Support for other vector stores might be added in the future.

## Enable RAG

The agent, by default, provides a basic, non-RAG, chat completion experience. To enable the RAG experience the following needs to be done:
1. A vector store collection should be created and hydrated with documents that the agent will use for retrieval.
2. The agent should be configured to use the collection for the retrieval process.

### Create and hydrate a vector store collection

The agent expects a vector store collection to have the following fields to be able to retrieve documents from it:
   
| Field Name | Data Type | Description |  
|------------|-----------|-------------|  
| chunk_id   | string/guid | The document key. The data type may vary depending on the vector store. |
| chunk      | string | Chunk from the document. |  
| title      | string | The document title or page title or page number. |  
| text_vector | float[] | Vector representation of the chunk. |

Each vector store has its own way for creating collections and filling them with documents. The following sections below describe how to do so for the supported vector stores.

#### Azure AI search  
   
To create a collection (index in Azure AI Search), follow this [Quickstart: Vectorize text and images in the Azure portal](https://learn.microsoft.com/en-us/azure/search/search-get-started-portal-import-vectors?tabs=sample-data-storage%2Cmodel-aoai%2Cconnect-data-storage) guide.
Use existing Azure resources, created during agent deployment, such as the Azure AI Search service, Azure OpenAI service, and the embedding model deployment instead of creating new ones.

### Configure the agent to use the vector store collection

To configure the agent to use the vector store collection created in the previous step, insert its name into the `CollectionName` property in the `appsettings.json` file of the `ChatWithAgent.AppHost` project:

```json  
"Rag": {
    ... other properties ...
    "CollectionName": "<collection name>",
}
```

## Connection strings

Some upstream dependencies require connection strings, which `azd` will prompt you for during deployment. Refer to the table below for the required formats:

| Dependency | Format                         | Example                                          |
|------------|--------------------------------|--------------------------------------------------|
| OpenAIChat     | `Endpoint=<uri>;Key=<key>`     | `Endpoint=https://api.openai.com/v1;Key=123` or `Key=123` |
| AzureOpenAI     | `Endpoint=<uri>;Key=<key>`     | `Endpoint=https://{account_name}.openai.azure.com;Key=123` or `Key=123` |
| AzureAISearch     | `Endpoint=<uri>;Key=<key>`     | `Endpoint=https://{search_service}.search.windows.net;Key=123` or `Key=123` |

When running agent locally, the connections string should be specified in user secrets. Please refer to the [Running the agent locally](#running-agent-locally) section for more information.


## Running agent locally

To run the agent locally, follow these steps:
1. Right-click on the `ChatWithAgent.AppHost` project in Visual Studio and select `Set as Startup Project`.  
2. Right-click on the `ChatWithAgent.AppHost` project in Visual Studio and select `Manage User Secrets` and add the connection strings for agent dependencies connection strings to the `ConnectionStrings` section.
    ```json
    {
      "ConnectionStrings": {
        "AzureOpenAI": "Endpoint=https://{account_name}.openai.azure.com",
        "AzureAISearch": "Endpoint=https://{search_service}.search.windows.net"
      }
    }
    ```
    The format for connection strings can be found in the [Connection Strings](#connection-strings) section above.

3. Go to the `Access control(IAM)` tab in the Azure OpenAI service on the Azure portal. Assign the `Cognitive Services OpenAI Contributor` role to the user authenticated with Azure CLI. This allows the agent to access the service on the user's behalf.
4. Go to the `Access control(IAM)` tab in the Azure AI Search service on the Azure portal. Assign the `Search Index Data Contributor` role to the user authenticated with Azure CLI. This allows the agent to access the service on the user's behalf.
5. Press `F5` to run the project.

## Clean up the resources

Run the `azd down` command, to clean up the resources. This command will delete all the resources provisioned for the agent.
 
## Billing

Visit the *Cost Management + Billing* page in Azure Portal to track current spend. For more information about how you're billed, and how you can monitor the costs incurred in your Azure subscriptions, visit [billing overview](https://learn.microsoft.com/azure/developer/intro/azure-developer-billing).

## Troubleshooting

Q: I visited the service endpoint listed, and I'm seeing a blank page, a generic welcome page, or an error page.

A: Your service may have failed to start, or it may be missing some configuration settings. To investigate further:

1. Run `azd show`. Click on the link under "View in Azure Portal" to open the resource group in Azure Portal.
2. Navigate to the specific Container App service that is failing to deploy.
3. Click on the failing revision under "Revisions with Issues".
4. Review "Status details" for more information about the type of failure.
5. Observe the log outputs from Console log stream and System log stream to identify any errors.
6. If logs are written to disk, use *Console* in the navigation to connect to a shell within the running container.

For more troubleshooting information, visit [Container Apps troubleshooting](https://learn.microsoft.com/azure/container-apps/troubleshooting). 

### Additional information

For additional information about setting up your `azd` project, visit our official [docs](https://learn.microsoft.com/azure/developer/azure-developer-cli/make-azd-compatible?pivots=azd-convert).