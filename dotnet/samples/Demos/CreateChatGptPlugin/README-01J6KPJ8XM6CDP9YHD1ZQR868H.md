---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:55:08Z
---

# Creating and using a OpenAI plugin

## Prerequisites

- [Azure Functions Core Tools](ht***********************************************ls) version 4.x.
- [.NET 6](ht********************************************.0) is required to run this sample.
- Install the recommended extensions
- [C#](ht*********************************************************************rp)
- [Semantic Kernel Tools](ht**********************************************************************************el) (optional)

You must also have the Azure Function located [here](./MathPlugin/) running locally, otherwise the sample will fail.

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](ht**************************************************************ts) to avoid the risk of leaking secrets into the repository, branches and pull requests.

This sample has been tested with the following models:

| Service      | Model type      | Model            | Model version | Supported |
| ------------ | --------------- | ---------------- | ------------: | --------- |
| OpenAI       | Text Completion | te************03 |             1 | ❌        |
| OpenAI       | Chat Completion | gp*********bo    |             1 | ❌        |
| OpenAI       | Chat Completion | gp*********bo    |          0301 | ❌        |
| Azure OpenAI | Chat Completion | gp*********bo    |          0613 | ✅        |
| Azure OpenAI | Chat Completion | gp*********bo    |          1106 | ✅        |
| OpenAI       | Chat Completion | gpt-4            |             1 | ❌        |
| OpenAI       | Chat Completion | gpt-4            |          0314 | ❌        |
| Azure OpenAI | Chat Completion | gpt-4            |          0613 | ✅        |
| Azure OpenAI | Chat Completion | gpt-4            |          1106 | ✅        |

This sample uses function calling, so it only works on models newer than 0613.

### Using .NET [Secret Manager](ht**************************************************************ts)

Configure an OpenAI endpoint

```powershell {"id":"01J6KPWER9SP48PCB1B2SQQ1VT"}
cd 14********************in/Solution

dotnet user-secrets set "Global:LlmService" "OpenAI"

dotnet user-secrets set "OpenAI:ModelType" "chat-completion"
dotnet user-secrets set "OpenAI:ChatCompletionModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "... your OpenAI key ..."
dotnet user-secrets set "OpenAI:OrgId" "... your ord ID ..."
```

Configure an Azure OpenAI endpoint

```powershell {"id":"01J6KPWERAMHRN5C9NEP175PZX"}
cd 14********************in/Solution

dotnet user-secrets set "Global:LlmService" "AzureOpenAI"

dotnet user-secrets set "AzureOpenAI:DeploymentType" "chat-completion"
dotnet user-secrets set "AzureOpenAI:ChatCompletionDeploymentName" "gp********bo"
dotnet user-secrets set "AzureOpenAI:ChatCompletionModelId" "gp**************13"
dotnet user-secrets set "AzureOpenAI:Endpoint" "... your Azure OpenAI endpoint ..."
dotnet user-secrets set "AzureOpenAI:ApiKey" "... your Azure OpenAI key ..."
```

## Running the sample

First, refer to the [README](./MathPlugin/README.md) in the MathPlugin\ folder
to start the Azure Function.

After starting the Azure Function and configuring the sample,
to build and run the console application, navigate to the [Solution](./Solution/) folder and hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell {"id":"01J6KPWERAMHRN5C9NET01NSTY"}
cd Solution
dotnet build
dotnet run
```
