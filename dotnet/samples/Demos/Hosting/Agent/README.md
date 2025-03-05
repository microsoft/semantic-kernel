# Agent Hosting

This folder contains a set of Aspire projects that demonstrate how to host a chat completion agent on Azure as a containerized service.

## Provision and Deploy
The following steps will guide you through provisioning, deploying, and cleaning up the resources required for the agent resources on Azure. All the steps below are described in detail here: [Deploy a .NET Aspire project to Azure Container Apps using the Azure Developer CLI (in-depth guide)
](https://learn.microsoft.com/en-us/dotnet/aspire/deployment/azure/aca-deployment-azd-in-depth?tabs=windows).

### Initialize the Project  

1. Open a terminal and navigate to the `Hosting\Agent` directory.
2. Initialize the project by running the `azd init` command. **azd** will inspect the directory structure and determine the type of the app.
3. Select the `Use code in the current directory` option when **azd** prompts you with two app initialization options.
4. Select the `Confirm and continue initializing my app` option to confirm that **azd** found the correct `ChatWithAgent.AppHost` project.
5. Enter an environment name which is used to name provisioned resources.

**azd** generates a number of files and places them into the working directory. These files are:
- `azure.yaml`: Describes the services of the app, such as the `ChatWithAgent.AppHost` project, and maps them to Azure resources.
- `.azure/config.json`: Configuration file that informs **azd** what the current active environment is.
- `.azure/{env-name}/.env`: Contains environment-specific overrides.

### Configure the Project  

Before deploying the agent to Azure, it's necessary to configure both the agent and its upstream dependencies, which include chat completion service and the vector store.
For detailed instructions on how to configure the agent and the dependencies, please refer to the [Configuration](#configuration) section.
 
### Deploy the project

1. Authenticate with Azure by running the `az login` command.
2. Provision all required resources and deploy the app to Azure by running the `azd up` command.
3. Select the subscription and location of the resources where the app will be deployed when prompted.
4. Provide required connection strings when prompted. More information on connection strings can be found in the [Connection strings](#connection-strings) section.
5. Copy the app endpoint URL from the output of the `azd up` command and paste it into a browser to see the app dashboard.
6. Click on the web frontend app link on the dashboard to navigate to the app and select the `Chat` tab to start chatting with the agent.

### Clean up the resources

1. To clean up the resources, run the `azd down` command. This command will delete all the resources provisioned for the app.

## Configuration

### Agent Configuration
   
To configure the agent, locate, open, and edit the `appsettings.json` file in the `ChatWithAgent.ApiService` project. The following settings are available:

```json
{
  "Agent": {
    "Name": "",
    "Description": "",  
    "Instructions": ""
  }
}
```

Configure the relevant properties:
- `Name`: This property defines the name of the agent. For example, `SupportBot` could be a name for an agent that provides customer support.
- `Description`: This property provides a brief description of the agent's role or purpose. For instance, `This bot assists users with support inquiries.` describes that the bot is intended to help users with their support-related questions.
- `Instructions`: This property gives specific instructions on how the agent should interact with users. An example could be, `Greet the user, ask how you can help, and provide solutions based on their questions.` This guides the agent on how to initiate conversations and respond to user inquiries.

### Chat Completion Model configuration

To configure the chat completion model, locate, open, and edit the `appsettings.json` file in the `ChatWithAgent.AppHost` project. The following settings are available:

```json
{
  "AIServices": {
    "AzureOpenAIChat": {
      "DeploymentName": "gpt-4o-mini",
      "ModelName": "gpt-4o-mini",
      "ModelVersion": "2024-07-18"
    },
    "OpenAIChat": {
      "ModelName": "gpt-4o-mini"
    }
  },
  "AIChatService": "AzureOpenAIChat"
}
```

#### 1. Choose the chat completion service
   
Set the `AIChatService` property to the chat completion service you want to use. The available services are:  
   
- `AzureOpenAIChat`: Azure OpenAI chat completion model.  
- `OpenAIChat`: OpenAI chat completion model.  
   
#### 2. Configure the Selected Chat Completion Model  
   
Depending on the selected service, configure the relevant properties:  
   
`AzureOpenAIChat`:  
- `DeploymentName`: The name of the deployment that hosts the chat completion model.  
- `ModelName`: The name of the chat completion model.  
- `ModelVersion`: The version of the chat completion model.  
   
`OpenAIChat`:  
- `ModelName`: The name of the chat completion model.  

### Text Embedding Model configuration

To configure the text embedding model, locate, open, and edit the `appsettings.json` file in the `ChatWithAgent.AppHost` project. The following settings are available:
```json
{
  "AIServices": {
    "AzureOpenAIEmbeddings": {
      "DeploymentName": "text-embedding-ada-002",
      "ModelName": "text-embedding-ada-002",
      "ModelVersion": "2"
    },
    "OpenAIEmbeddings": {
      "ModelName": "text-embedding-ada-002"
    }
  },
  "AIEmbeddingsService": "OpenAIEmbeddings"
}
```

#### 1. Choose the text embedding service

Set the `AIEmbeddingsService` property to the text embedding service you want to use. The available services are:
    - `AzureOpenAIEmbeddings`: Azure OpenAI text embedding model.
    - `OpenAIEmbeddings`: OpenAI text embedding model.

#### 2. Configure the Selected Text Embedding Model

Depending on the selected service, configure the relevant properties:

`AzureOpenAIEmbeddings`:
- `DeploymentName`: The name of the deployment that hosts the text embedding model.
- `ModelName`: The name of the text embedding model.
- `ModelVersion`: The version of the text embedding model.

`OpenAIEmbeddings`:
- `ModelName`: The name of the text embedding model.

### Vector Store Configuration
`TBD`

## Connection strings

Some upstream dependencies require connection strings, which `azd` will prompt you for during deployment. Refer to the table below for the required formats:

| Dependency | Format                         | Example                                          |
|------------|--------------------------------|--------------------------------------------------|
| OpenAIChat     | `Endpoint=<uri>;Key=<key>`     | `Endpoint=https://api.openai.com/v1;Key=123` or `Key=123` |

When running agent locally, the connections string should be specified in user secrets. Please refer to the [Running the agent locally](#running-the-agent-locally) section for more information.


## Running the agent locally

To run the agent locally, follow these steps:
1. Right-click on the `ChatWithAgent.AppHost` project in Visual Studio and select `Set as Startup Project`.  
2. Right-click on the `ChatWithAgent.AppHost` project in Visual Studio and select `Manage User Secrets` and add the agent dependencies connection strings to the `ConnectionStrings` section.
    ```json
    {
      "ConnectionStrings": {
        "OpenAIChat": "Endpoint=https://api.openai.com/v1;Key=123"
      }
    }
    ```
    The format for connection strings can be found in the [Connection Strings](#connection-strings) section above.

3. Press `F5` to run the project.

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