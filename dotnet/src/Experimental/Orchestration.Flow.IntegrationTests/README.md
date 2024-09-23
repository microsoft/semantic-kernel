<<<<<<< HEAD
# Experimental Flow Orchestrator Integration Tests
=======
﻿# Experimental Flow Orchestrator Integration Tests
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

## Requirements

1. **Azure OpenAI**: go to the [Azure OpenAI Quickstart](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart)
<<<<<<< HEAD
<<<<<<< HEAD
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
=======
   and deploy an instance of Azure OpenAI, deploy a model like "gpt-35-turbo-instruct" find your Endpoint and API key.
>>>>>>> origin/111
2. **OpenAI**: go to [OpenAI](https://platform.openai.com) to register and procure your API key.
=======
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
2. **OpenAI**: go to [OpenAI](https://openai.com/product/) to register and procure your API key.
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
3. **Azure Bing Web Search API**: go to [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
   and select `Try Now` to get started.

## Setup

### Option 1: Use Secret Manager

Integration tests will require secrets and credentials, to access OpenAI, Azure OpenAI,
<<<<<<< HEAD
Bing and other resources.
=======
Bing and other resources. 
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

<<<<<<< HEAD
```sh {"id":"01J6KPR1FAFBFPM4TCN6WEPFNE"}
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-gpt-35-turbo-instruct"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "gpt-35-turbo-instruct"
=======
```
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "text-davinci-003"
dotnet user-secrets set "OpenAI:ModelId" "text-davinci-003"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-text-davinci-003"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "text-davinci-003"
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "gpt-4"
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIEmbeddings:ServiceId" "azure-text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "text-embedding-ada-002"
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "https://contoso.openai.azure.com/"
dotnet user-secrets set "AzureOpenAIEmbeddings:ApiKey" "..."

dotnet user-secrets set "Bing:ApiKey" "..."
```

### Option 2: Use Configuration File
<<<<<<< HEAD

1. Create a `testsettings.development.json` file next to `testsettings.json`. This file will be ignored by git,
   the content will not end up in pull requests, so it's safe for personal settings. Keep the file safe.
2. Edit `testsettings.development.json` and
   1. set you Azure OpenAI and OpenAI keys and settings found in Azure portal and OpenAI website.
   2. set the `Bing:ApiKey` using the API key you can find in the Azure portal.

For example:

```json {"id":"01J6KPR1FAFBFPM4TCN86NXX8S"}
{
  "OpenAI": {
    "ServiceId": "gpt-3.5-turbo-instruct",
    "ModelId": "gpt-3.5-turbo-instruct",
=======
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
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
    "ChatModelId": "gpt-4",
    "ApiKey": "sk-...."
  },
  "AzureOpenAI": {
<<<<<<< HEAD
    "ServiceId": "gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
=======
    "ServiceId": "azure-text-davinci-003",
    "DeploymentName": "text-davinci-003",
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
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
  "Bing": {
    "ApiKey": "...."
  }
}
```

### Option 3: Use Environment Variables
<<<<<<< HEAD

=======
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
You may also set the test settings in your environment variables. The environment variables will override the settings in the `testsettings.development.json` file.

When setting environment variables, use a double underscore (i.e. "\_\_") to delineate between parent and child properties. For example:

- bash:

<<<<<<< HEAD
```bash {"id":"01J6KPR1FBXXPNFHK1MXCK9QN7"}
export OpenAI__ApiKey="sk-...."
export AzureOpenAI__ApiKey="...."
export AzureOpenAI__DeploymentName="gpt-35-turbo-instruct"
export AzureOpenAI__ChatDeploymentName="gpt-4"
export AzureOpenAIEmbeddings__DeploymentName="azure-text-embedding-ada-002"
export AzureOpenAI__Endpoint="https://contoso.openai.azure.com/"
export Bing__ApiKey="...."
```

- PowerShell:

```ps {"id":"01J6KPR1FBXXPNFHK1MXX8YDH7"}
$env:OpenAI__ApiKey = "sk-...."
$env:AzureOpenAI__ApiKey = "...."
$env:AzureOpenAI__DeploymentName = "gpt-35-turbo-instruct"
$env:AzureOpenAI__ChatDeploymentName = "gpt-4"
$env:AzureOpenAIEmbeddings__DeploymentName = "azure-text-embedding-ada-002"
$env:AzureOpenAI__Endpoint = "https://contoso.openai.azure.com/"
$env:Bing__ApiKey = "...."
```
=======
  ```bash
  export OpenAI__ApiKey="sk-...."
  export AzureOpenAI__ApiKey="...."
  export AzureOpenAI__DeploymentName="azure-text-davinci-003"
  export AzureOpenAI__ChatDeploymentName="gpt-4"
  export AzureOpenAIEmbeddings__DeploymentName="azure-text-embedding-ada-002"
  export AzureOpenAI__Endpoint="https://contoso.openai.azure.com/"
  export Bing__ApiKey="...."
  ```

- PowerShell:

  ```ps
  $env:OpenAI__ApiKey = "sk-...."
  $env:AzureOpenAI__ApiKey = "...."
  $env:AzureOpenAI__DeploymentName = "azure-text-davinci-003"
  $env:AzureOpenAI__ChatDeploymentName = "gpt-4"
  $env:AzureOpenAIEmbeddings__DeploymentName = "azure-text-embedding-ada-002"
  $env:AzureOpenAI__Endpoint = "https://contoso.openai.azure.com/"
  $env:Bing__ApiKey = "...."
  ```
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
