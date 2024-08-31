# Integration Tests

## Requirements

1. **Azure OpenAI**: go to the [Azure OpenAI Quickstart](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart)
   and deploy an instance of Azure OpenAI, deploy a model like "gpt-35-turbo-instruct" find your Endpoint and API key.
2. **OpenAI**: go to [OpenAI](https://platform.openai.com) to register and procure your API key.
3. **HuggingFace API key**: see https://huggingface.co/docs/huggingface_hub/guides/inference for details.
4. **Azure Bing Web Search API**: go to [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
   and select `Try Now` to get started.
5. **Postgres**: start a postgres with the [pgvector](https://github.com/pgvector/pgvector) extension installed. You can easily do it using the docker image [ankane/pgvector](https://hub.docker.com/r/ankane/pgvector).
6. **Weaviate**: go to `IntegrationTests/Connectors/Weaviate` where `docker-compose.yml` is located and run `docker-compose up --build`. 

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

dotnet user-secrets set "OpenAI:ServiceId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "OpenAITextToImage:ServiceId" "dall-e-3"
dotnet user-secrets set "OpenAITextToImage:ModelId" "dall-e-3"
dotnet user-secrets set "OpenAITextToImage:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-gpt-35-turbo-instruct"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "gpt-35-turbo-instruct"
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "gpt-4"
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIEmbeddings:ServiceId" "azure-text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAIEmbeddings:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIAudioToText:ServiceId" "azure-audio-to-text"
dotnet user-secrets set "AzureOpenAIAudioToText:DeploymentName" "whisper-1"
dotnet user-secrets set "AzureOpenAIAudioToText:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAIAudioToText:ApiKey" "..."

dotnet user-secrets set "AzureOpenAITextToAudio:ServiceId" "azure-text-to-audio"
dotnet user-secrets set "AzureOpenAITextToAudio:DeploymentName" "tts-1"
dotnet user-secrets set "AzureOpenAITextToAudio:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAITextToAudio:ApiKey" "..."

dotnet user-secrets set "AzureOpenAITextToImage:ServiceId" "azure-text-to-image"
dotnet user-secrets set "AzureOpenAITextToImage:DeploymentName" "dall-e-3"
dotnet user-secrets set "AzureOpenAITextToImage:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAITextToImage:ApiKey" "..."

dotnet user-secrets set "MistralAI:ChatModel" "mistral-large-latest"
dotnet user-secrets set "MistralAI:EmbeddingModel" "mistral-embed"
dotnet user-secrets set "MistralAI:ApiKey" "..."

dotnet user-secrets set "HuggingFace:ApiKey" "..."
dotnet user-secrets set "Bing:ApiKey" "..."
dotnet user-secrets set "Postgres:ConnectionString" "..."

dotnet user-secrets set "Planners:AzureOpenAI:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "Planners:AzureOpenAI:ChatDeploymentName" "gpt-4-1106-preview"
dotnet user-secrets set "Planners:AzureOpenAI:ServiceId" "gpt-4-1106-preview"
dotnet user-secrets set "Planners:AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "Planners:OpenAI:ModelId" "gpt-3.5-turbo-1106"
dotnet user-secrets set "Planners:OpenAI:ApiKey" "..."
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
    "ServiceId": "gpt-3.5-turbo-instruct",
    "ModelId": "gpt-3.5-turbo-instruct",
    "ChatModelId": "gpt-4",
    "ApiKey": "sk-...."
  },
  "AzureOpenAI": {
    "ServiceId": "azure-gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
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
  export AzureOpenAI__DeploymentName="gpt-35-turbo-instruct"
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
  $env:AzureOpenAI__DeploymentName = "gpt-35-turbo-instruct"
  $env:AzureOpenAI__ChatDeploymentName = "gpt-4"
  $env:AzureOpenAIEmbeddings__DeploymentName = "azure-text-embedding-ada-002"
  $env:AzureOpenAI__Endpoint = "https://contoso.openai.azure.com/"
  $env:HuggingFace__ApiKey = "...."
  $env:Bing__ApiKey = "...."
  $env:Postgres__ConnectionString = "...."
  ```
