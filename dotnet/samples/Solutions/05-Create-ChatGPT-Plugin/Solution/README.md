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

The sample can be configured by using either:

- Enter secrets at the command line with [.NET Secret Manager](#using-net-secret-manager)
- Enter secrets in [appsettings.json](#using-appsettingsjson)

For Debugging the console application alone, we suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

Configure an OpenAI endpoint

```powershell
cd 05-Create-ChatGPT-Plugin/Solution
dotnet user-secrets set "endpointType" "text-completion"
dotnet user-secrets set "serviceType" "OpenAI"
dotnet user-secrets set "serviceId" "text-davinci-003"
dotnet user-secrets set "deploymentOrModelId" "text-davinci-003"
dotnet user-secrets set "apiKey" "... your OpenAI key ..."
```

Configure an Azure OpenAI endpoint

```powershell
cd 05-Create-ChatGPT-Plugin/Solution
dotnet user-secrets set "endpointType" "text-completion"
dotnet user-secrets set "serviceType" "AzureOpenAI"
dotnet user-secrets set "serviceId" "text-davinci-003"
dotnet user-secrets set "deploymentOrModelId" "text-davinci-003"
dotnet user-secrets set "endpoint" "https:// ... your endpoint ... .openai.azure.com/"
dotnet user-secrets set "apiKey" "... your Azure OpenAI key ..."
```

Configure the Semantic Kernel logging level

```powershell
dotnet user-secrets set "LogLevel" 0
```

Log levels:

- 0 = Trace
- 1 = Debug
- 2 = Information
- 3 = Warning
- 4 = Error
- 5 = Critical
- 6 = None

### Using appsettings.json

Configure an OpenAI endpoint

1. Copy [settings.json.openai-example](./config/appsettings.json.openai-example) to `./Config/appsettings.json`
1. Edit the file to add your OpenAI endpoint configuration

Configure an Azure OpenAI endpoint

1. Copy [settings.json.azure-example](./config/appsettings.json.azure-example) to `./Config/appsettings.json`
1. Edit the file to add your Azure OpenAI endpoint configuration

## Running the sample

Before running the sample, make sure you have the [Math Plugin](../MathPlugin/) running locally.

To run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```
