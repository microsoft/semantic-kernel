# Time Plugin - Demo Application

This is an example how you can easily use Plugins with the Power of Auto Function Calling from AI Models. 

Here we have a simple Time Plugin created in C# that can be called from the AI Model to get the current time.


## Semantic Kernel Features Used

- [Plugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Functions/KernelPlugin.cs) - Creating a Plugin from a native C# Booking class to be used by the Kernel to interact with Bookings API.
- [Chat Completion Service](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service [OpenAI Connector implementation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/ChatCompletion/OpenAIChatCompletionService.cs) to generate responses from the LLM.
- [Chat History](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/ChatHistory.cs) Using the Chat History abstraction to create, update and retrieve chat history from Chat Completion Models.
- [Auto Function Calling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/AutoFunctionCalling/OpenAI_FunctionCalling.cs) Enables the LLM to have knowledge of current importedUsing the Function Calling feature automatically call the Booking Plugin from the LLM.

## Prerequisites

- [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0).

### Function Calling Enabled Models

This sample uses function calling capable models and has been tested with the following models:

| Model type      | Model name/id             |       Model version | Supported |
| --------------- | ------------------------- | ------------------: | --------- |
| Chat Completion | gpt-3.5-turbo             |                0125 | ✅        |
| Chat Completion | gpt-3.5-turbo-1106        |                1106 | ✅        |
| Chat Completion | gpt-3.5-turbo-0613        |                0613 | ✅        |
| Chat Completion | gpt-3.5-turbo-0301        |                0301 | ❌        |
| Chat Completion | gpt-3.5-turbo-16k         |                0613 | ✅        |
| Chat Completion | gpt-4                     |                0613 | ✅        |
| Chat Completion | gpt-4-0613                |                0613 | ✅        |
| Chat Completion | gpt-4-0314                |                0314 | ❌        |
| Chat Completion | gpt-4-turbo               |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-2024-04-09    |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-preview       |        0125-preview | ✅        |
| Chat Completion | gpt-4-0125-preview        |        0125-preview | ✅        |
| Chat Completion | gpt-4-vision-preview      | 1106-vision-preview | ✅        |
| Chat Completion | gpt-4-1106-vision-preview | 1106-vision-preview | ✅        |

ℹ️ OpenAI Models older than 0613 version do not support function calling.

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

```powershell

# OpenAI 
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-3.5-turbo"
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```

### Example of a conversation

Ask questions to use the Time Plugin such as:
- What time is it?

**User** > What time is it ?

**Assistant** > The current time is Sun, 12 May 2024 15:53:54 GMT.

