# Creating and using a ChatGPT plugin

The `05-Create-ChatGPT-Plugin` console application shows the final solution to the [ChatGPT plugin](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chatgpt-plugins) doc article.

## Prerequisites

- [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools) version 4.x.
- [.NET 6](https://dotnet.microsoft.com/download/dotnet/6.0) is required to run this sample.
- Install the recommended extensions
- [C#](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csharp)
- [Semantic Kernel Tools](https://marketplace.visualstudio.com/items?itemName=ms-semantic-kernel.semantic-kernel) (optional)

You must also have the Azure Function located [here](../MathPlugin/) running locally, otherwise the sample will fail.

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

This sample has been tested with the following models:

| Service      | Model type      | Model            | Model version | Supported |
| ------------ | --------------- | ---------------- | ------------: | --------- |
| OpenAI       | Text Completion | text-davinci-003 |             1 | ❌        |
| OpenAI       | Chat Completion | gpt-3.5-turbo    |             1 | ✅        |
| OpenAI       | Chat Completion | gpt-3.5-turbo    |          0301 | ✅        |
| OpenAI       | Chat Completion | gpt-4            |             1 | ✅        |
| OpenAI       | Chat Completion | gpt-4            |          0314 | ✅        |
| Azure OpenAI | Text Completion | text-davinci-003 |             1 | ❌        |
| Azure OpenAI | Chat Completion | gpt-3.5-turbo    |          0301 | ✅        |
| Azure OpenAI | Chat Completion | gpt-4-0314       |          0314 | ✅        |

Only the GPT-4 models are "smart" enough to call the `GetLogicalValue` function.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

Configure an OpenAI endpoint

```powershell
cd 05-Create-ChatGPT-Plugin/Solution

dotnet user-secrets set "Global:LlmService" "OpenAI"

dotnet user-secrets set "OpenAI:ModelType" "chat-completion"
dotnet user-secrets set "OpenAI:ChatCompletionModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "... your OpenAI key ..."
```

Configure an Azure OpenAI endpoint

```powershell
cd 05-Create-ChatGPT-Plugin/Solution

dotnet user-secrets set "Global:LlmService" "OpenAI"

dotnet user-secrets set "AzureOpenAI:DeploymentType" "chat-completion"
dotnet user-secrets set "AzureOpenAI:ChatCompletionDeploymentName" "gpt-4"
dotnet user-secrets set "AzureOpenAI:Endpoint" "... your Azure OpenAI endpoint ..."
dotnet user-secrets set "AzureOpenAI:ApiKey" "... your Azure OpenAI key ..."
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```
