<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Experimental Flow Orchestrator Integration Tests
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
# Experimental Flow Orchestrator Integration Tests
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
# Experimental Flow Orchestrator Integration Tests
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
# Experimental Flow Orchestrator Integration Tests
=======
﻿# Experimental Flow Orchestrator Integration Tests
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

## Requirements

1. **Azure OpenAI**: go to the [Azure OpenAI Quickstart](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
=======
   and deploy an instance of Azure OpenAI, deploy a model like "gpt-35-turbo-instruct" find your Endpoint and API key.
>>>>>>> origin/111
2. **OpenAI**: go to [OpenAI](https://platform.openai.com) to register and procure your API key.
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
=======
   and deploy an instance of Azure OpenAI, deploy a model like "gpt-35-turbo-instruct" find your Endpoint and API key.
>>>>>>> origin/111
2. **OpenAI**: go to [OpenAI](https://platform.openai.com) to register and procure your API key.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
   and deploy an instance of Azure OpenAI, deploy a model like "text-davinci-003" find your Endpoint and API key.
2. **OpenAI**: go to [OpenAI](https://openai.com/product/) to register and procure your API key.
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
3. **Azure Bing Web Search API**: go to [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
   and select `Try Now` to get started.

## Setup

### Option 1: Use Secret Manager

Integration tests will require secrets and credentials, to access OpenAI, Azure OpenAI,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
Bing and other resources.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
Bing and other resources.
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
Bing and other resources.
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
Bing and other resources.
=======
Bing and other resources. 
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
```sh {"id":"01J6KPR1FAFBFPM4TCN6WEPFNE"}
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
```sh {"id":"01J6KPR1FAFBFPM4TCN6WEPFNE"}
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-gpt-35-turbo-instruct"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "gpt-35-turbo-instruct"
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
```
>>>>>>> origin/main
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

<<<<<<< main
dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-gpt-35-turbo-instruct"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "gpt-35-turbo-instruct"
=======
dotnet user-secrets set "AzureOpenAI:ServiceId" "azure-text-davinci-003"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "text-davinci-003"
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
1. Create a `testsettings.development.json` file next to `testsettings.json`. This file will be ignored by git,
   the content will not end up in pull requests, so it's safe for personal settings. Keep the file safe.
2. Edit `testsettings.development.json` and
   1. set you Azure OpenAI and OpenAI keys and settings found in Azure portal and OpenAI website.
   2. set the `Bing:ApiKey` using the API key you can find in the Azure portal.

For example:

```json {"id":"01J6KPR1FAFBFPM4TCN86NXX8S"}
{
  "OpenAI": {
<<<<<<< main
    "ServiceId": "gpt-3.5-turbo-instruct",
    "ModelId": "gpt-3.5-turbo-instruct",
=======
    "ServiceId": "text-davinci-003",
    "ModelId": "text-davinci-003",
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    "ChatModelId": "gpt-4",
    "ApiKey": "sk-...."
  },
  "AzureOpenAI": {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    "ServiceId": "gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    "ServiceId": "gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    "ServiceId": "gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
=======
    "ServiceId": "azure-text-davinci-003",
    "DeploymentName": "text-davinci-003",
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

=======
=======
>>>>>>> origin/main
=======
<<<<<<< main

=======
>>>>>>> Stashed changes
<<<<<<< HEAD

=======
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
You may also set the test settings in your environment variables. The environment variables will override the settings in the `testsettings.development.json` file.

When setting environment variables, use a double underscore (i.e. "\_\_") to delineate between parent and child properties. For example:

- bash:

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
```bash {"id":"01J6KPR1FBXXPNFHK1MXCK9QN7"}
export OpenAI__ApiKey="sk-...."
export AzureOpenAI__ApiKey="...."
export AzureOpenAI__DeploymentName="gpt-35-turbo-instruct"
export AzureOpenAI__ChatDeploymentName="gpt-4"
export AzureOpenAIEmbeddings__DeploymentName="azure-text-embedding-ada-002"
export AzureOpenAI__Endpoint="https://contoso.openai.azure.com/"
export Bing__ApiKey="...."
```
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
