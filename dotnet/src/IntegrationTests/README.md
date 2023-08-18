# Azure/OpenAI Skill Integration Tests

## Requirements

1. **Azure OpenAI**: go to the [Azure OpenAI Quickstart](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart)
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
2. **OpenAI**: go to [OpenAI](https://openai.com/api/) to register and procure your API key.
3. **HuggingFace API key**: see https://huggingface.co/docs/huggingface_hub/guides/inference for details.
4. **Azure Bing Web Search API**: go to [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
   and select `Try Now` to get started.
5. **Oobabooga Text generation web UI**: Follow the [installation instructions](https://github.com/oobabooga/text-generation-webui#installation) to get a local Oobabooga instance running. Follow the [download instructions](https://github.com/oobabooga/text-generation-webui#downloading-models) to install a test model e.g. `python download-model.py gpt2`. Follow the [starting instructions](https://github.com/oobabooga/text-generation-webui#starting-the-web-ui) to start your local instance, enabling API, e.g. `python server.py --model gpt2 --listen --api --api-blocking-port "5000" --api-streaming-port "5005"`. Note that `--model` parameter is optional and models can be downloaded and hot swapped using exclusively the web UI, making it easy to test various models.
6. **Postgres**: start a postgres with the [pgvector](https://github.com/pgvector/pgvector) extension installed. You can easily do it using the docker image [ankane/pgvector](https://hub.docker.com/r/ankane/pgvector).
7. **MultiConnector**: See the [detailed instructions](/Connectors/MultiConnector/). 

## Setup

### Option 1: Use Secret Manager

Integration tests will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. 

We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "text-davinci-003"
dotnet user-secrets set "OpenAI:ModelId" "text-davinci-003"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-text-davinci-003"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "text-davinci-003"
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "gpt-4"
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIEmbeddings:ServiceId" "azure-text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAIEmbeddings:ApiKey" "..."

dotnet user-secrets set "HuggingFace:ApiKey" "..."
dotnet user-secrets set "Bing:ApiKey" "..."
dotnet user-secrets set "Postgres:ConnectionString" "..."
```

### Option 2: Use Configuration File
1. Create a `testsettings.development.json` file next to `testsettings.json`. This file will be ignored by git,
   the content will not end up in pull requests, so it's safe for personal settings. Keep the file safe.
2. Edit `testsettings.development.json` and
    1. set you Azure OpenAI and OpenAI keys and settings found in Azure portal and OpenAI website.
    2. set the `Bing:ApiKey` using the API key you can find in the Azure portal.

For example:

```json
{
  "OpenAI": {
    "ServiceId": "text-davinci-003",
    "ModelId": "text-davinci-003",
    "ChatModelId": "gpt-4",
    "ApiKey": "sk-...."
  },
  "AzureOpenAI": {
    "ServiceId": "azure-text-davinci-003",
    "DeploymentName": "text-davinci-003",
    "ChatDeploymentName": "gpt-4",
    "Endpoint": "https://contoso.openai.azure.com/",
    "ApiKey": "...."
  },
  "OpenAIEmbeddings": {
    "ServiceId": "text-embedding-ada-002",
    "ModelId": "text-embedding-ada-002",
    "ApiKey": "sk-...."
  },
  "AzureOpenAIEmbeddings": {
    "ServiceId": "azure-text-embedding-ada-002",
    "DeploymentName": "text-embedding-ada-002",
    "Endpoint": "https://contoso.openai.azure.com/",
    "ApiKey": "...."
  },
  "HuggingFace": {
    "ApiKey": ""
  },
  "Bing": {
    "ApiKey": "...."
  },
  "Postgres": {
    "ConnectionString": "Host=localhost;Database=postgres;User Id=postgres;Password=mysecretpassword"
  }
}
```

### Option 3: Use Environment Variables
You may also set the test settings in your environment variables. The environment variables will override the settings in the `testsettings.development.json` file.

When setting environment variables, use a double underscore (i.e. "\_\_") to delineate between parent and child properties. For example:

- bash:

  ```bash
  export OpenAI__ApiKey="sk-...."
  export AzureOpenAI__ApiKey="...."
  export AzureOpenAI__DeploymentName="azure-text-davinci-003"
  export AzureOpenAI__ChatDeploymentName="gpt-4"
  export AzureOpenAIEmbeddings__DeploymentName="azure-text-embedding-ada-002"
  export AzureOpenAI__Endpoint="https://contoso.openai.azure.com/"
  export HuggingFace__ApiKey="...."
  export Bing__ApiKey="...."
  export Postgres__ConnectionString="...."
  ```

- PowerShell:

  ```ps
  $env:OpenAI__ApiKey = "sk-...."
  $env:AzureOpenAI__ApiKey = "...."
  $env:AzureOpenAI__DeploymentName = "azure-text-davinci-003"
  $env:AzureOpenAI__ChatDeploymentName = "gpt-4"
  $env:AzureOpenAIEmbeddings__DeploymentName = "azure-text-embedding-ada-002"
  $env:AzureOpenAI__Endpoint = "https://contoso.openai.azure.com/"
  $env:HuggingFace__ApiKey = "...."
  $env:Bing__ApiKey = "...."
  $env:Postgres__ConnectionString = "...."
  ```
