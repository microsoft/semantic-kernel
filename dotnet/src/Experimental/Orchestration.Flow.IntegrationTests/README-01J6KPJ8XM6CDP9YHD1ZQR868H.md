---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:52:47Z
---

# Experimental Flow Orchestrator Integration Tests

## Requirements

1. **Azure OpenAI**: go to the [Azure OpenAI Quickstart](ht************************************************************************rt)
   and deploy an instance of Azure OpenAI, deploy a model like "gp*****************ct" find your Endpoint and API key.
2. **OpenAI**: go to [OpenAI](ht***********************om) to register and procure your API key.
3. **Azure Bing Web Search API**: go to [Bing Web Search API](ht*********************************************************pi)
   and select `Try Now` to get started.

## Setup

### Option 1: Use Secret Manager

Integration tests will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources.

We suggest using .NET [Secret Manager](ht**************************************************************ts)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```sh {"id":"01J6KPR1FAFBFPM4TCN6WEPFNE"}
cd dotnet/src/IntegrationTests

dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "gp******************ct"
dotnet user-secrets set "OpenAI:ModelId" "gp******************ct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "az***********************ct"
dotnet user-secrets set "AzureOpenAI:DeploymentName" "gp*****************ct"
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "gpt-4"
dotnet user-secrets set "AzureOpenAI:Endpoint" "ht****************************om/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIEmbeddings:ServiceId" "az************************02"
dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "te******************02"
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "ht****************************om/"
dotnet user-secrets set "AzureOpenAIEmbeddings:ApiKey" "..."

dotnet user-secrets set "Bing:ApiKey" "..."
```

### Option 2: Use Configuration File

1. Create a `testsettings.development.json` file next to `testsettings.json`. This file will be ignored by git,
   the content will not end up in pull requests, so it's safe for personal settings. Keep the file safe.
2. Edit `testsettings.development.json` and
   1. set you Azure OpenAI and OpenAI keys and settings found in Azure portal and OpenAI website.
   2. set the `Bing:ApiKey` using the API key you can find in the Azure portal.

For example:

```json {"id":"01J6KPR1FAFBFPM4TCN86NXX8S"}
{"OpenAI":{"ServiceId":"gp******************ct","ModelId":"gp******************ct","ChatModelId":"gpt-4","ApiKey":"sk***.."},"AzureOpenAI":{"ServiceId":"gp*****************ct","DeploymentName":"gp*****************ct","ChatDeploymentName":"gpt-4","Endpoint":"ht****************************om/","ApiKey":"****"},"OpenAIEmbeddings":{"ServiceId":"te******************02","ModelId":"te******************02","ApiKey":"sk***.."},"AzureOpenAIEmbeddings":{"ServiceId":"az************************02","DeploymentName":"te******************02","Endpoint":"ht****************************om/","ApiKey":"****"},"Bing":{"ApiKey":"****"}}
```

### Option 3: Use Environment Variables

You may also set the test settings in your environment variables. The environment variables will override the settings in the `testsettings.development.json` file.

When setting environment variables, use a double underscore (i.e. "\_\_") to delineate between parent and child properties. For example:

- bash:

```bash {"id":"01J6KPR1FBXXPNFHK1MXCK9QN7"}
export OpenAI__ApiKey="sk-...."
export AzureOpenAI__ApiKey="...."
export Az***********************me="gp*****************ct"
export Az***************************me="gpt-4"
export AzureOpenAIEmbeddings__DeploymentName="az************************02"
export AzureOpenAI__Endpoint="ht****************************om/"
export Bing__ApiKey="...."
```

- PowerShell:

```ps {"id":"01J6KPR1FBXXPNFHK1MXX8YDH7"}
$env:OpenAI__ApiKey = "sk-...."
$env:AzureOpenAI__ApiKey = "...."
$env:AzureOpenAI__DeploymentName = "gp*****************ct"
$env:AzureOpenAI__ChatDeploymentName = "gpt-4"
$env:AzureOpenAIEmbeddings__DeploymentName = "az************************02"
$env:AzureOpenAI__Endpoint = "ht****************************om/"
$env:Bing__ApiKey = "...."
```
