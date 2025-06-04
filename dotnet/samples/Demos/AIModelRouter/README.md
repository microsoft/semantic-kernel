# AI Model Router

This sample demonstrates how to implement an AI Model Router using Semantic Kernel connectors to direct requests to various AI models based on user input. As part of this example we integrate LMStudio, Ollama, and OpenAI, utilizing the OpenAI Connector for LMStudio and Ollama due to their compatibility with the OpenAI API.

> [!IMPORTANT]
> You can modify to use any other combination of connector or OpenAI compatible API model provider.

## Semantic Kernel Features Used

- [Chat Completion Service](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service [OpenAI Connector implementation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/Services/OpenAIChatCompletionService.cs) to generate responses from the LLM.
- [Filters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs), using to capture selected service and log in the console.

## Prerequisites

- [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0).

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

```powershell
dotnet user-secrets set "OpenAI:ApiKey" ".. api key .."
dotnet user-secrets set "OpenAI:ChatModelId" ".. chat completion model .." (default: gpt-4o)
dotnet user-secrets set "AzureOpenAI:Endpoint" ".. endpoint .."
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" ".. chat deployment name .." (default: gpt-4o)
dotnet user-secrets set "AzureOpenAI:ApiKey" ".. api key .." (default: Authenticate with Azure CLI credential)
dotnet user-secrets set "AzureAIInference:ApiKey" ".. api key .."
dotnet user-secrets set "AzureAIInference:Endpoint" ".. endpoint .."
dotnet user-secrets set "AzureAIInference:ChatModelId" ".. chat completion model .."
dotnet user-secrets set "LMStudio:Endpoint" ".. endpoint .." (default: http://localhost:1234)
dotnet user-secrets set "Ollama:ModelId" ".. model id .."
dotnet user-secrets set "Ollama:Endpoint" ".. endpoint .." (default: http://localhost:11434)
dotnet user-secrets set "Onnx:ModelId" ".. model id .."
dotnet user-secrets set "Onnx:ModelPath" ".. model folder path .."
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```

### Example of a conversation

> **User** > OpenAI, what is Jupiter? Keep it simple.

> **Assistant** > Sure! Jupiter is the largest planet in our solar system. It's a gas giant, mostly made of hydrogen and helium, and it has a lot of storms, including the famous Great Red Spot. Jupiter also has at least 79 moons.

> **User** > Ollama, what is Jupiter? Keep it simple.

> **Assistant** > Jupiter is a giant planet in our solar system known for being the largest and most massive, famous for its spectacled clouds and dozens of moons including Ganymede which is bigger than Earth!

> **User** > LMStudio, what is Jupiter? Keep it simple.

> **Assistant** > Jupiter is the fifth planet from the Sun in our Solar System and one of its gas giants alongside Saturn, Uranus, and Neptune. It's famous for having a massive storm called the Great Red Spot that has been raging for hundreds of years.