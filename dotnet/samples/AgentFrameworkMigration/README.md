# Semantic Kernel to Agent Framework Migration Guide

## What's Changed?
- **Namespace Updates**: From `Microsoft.SemanticKernel.Agents` to `Microsoft.Agents.AI`
- **Agent Creation**: Single fluent API calls vs multi-step builder patterns
- **Thread Management**: Built-in thread management vs manual thread creation
- **Tool Registration**: Direct function registration vs plugin wrapper systems
- **Dependency Injection**: Simplified service registration patterns
- **Invocation Patterns**: Streamlined options and result handling

## Benefits of Migration
- **Simplified API**: Reduced complexity and boilerplate code
- **Better Performance**: Optimized object creation and memory usage
- **Unified Interface**: Consistent patterns across different AI providers
- **Enhanced Developer Experience**: More intuitive and discoverable APIs

## Key Changes

### 1. Namespace Updates

#### Semantic Kernel

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
```

#### Agent Framework

Agent Framework namespaces are under `Microsoft.Agents.AI`.
Agent Framework uses the core AI message and content types from `Microsoft.Extensions.AI` for communication between components.

```csharp
using Microsoft.Extensions.AI;
using Microsoft.Agents.AI;
```

### 2. Agent Creation Simplification

#### Semantic Kernel

Every agent in Semantic Kernel depends on a `Kernel` instance and will have 
an empty `Kernel` if not provided.

```csharp
 Kernel kernel = Kernel
    .AddOpenAIChatClient(modelId, apiKey)
    .Build();

 ChatCompletionAgent agent = new() { Instructions = ParrotInstructions, Kernel = kernel };
```

Azure AI Foundry requires an agent resource to be created in the cloud before creating a local agent class that uses it.

```csharp
PersistentAgentsClient azureAgentClient = AzureAIAgent.CreateAgentsClient(azureEndpoint, new AzureCliCredential());

PersistentAgent definition = await azureAgentClient.Administration.CreateAgentAsync(
    deploymentName,
    instructions: ParrotInstructions);

AzureAIAgent agent = new(definition, azureAgentClient);
 ```

#### Agent Framework

Agent creation in Agent Framework is made simpler with extensions provided by all main providers.

```csharp
AIAgent openAIAgent = chatClient.CreateAIAgent(instructions: ParrotInstructions);
AIAgent azureFoundryAgent = await persistentAgentsClient.CreateAIAgentAsync(instructions: ParrotInstructions);
AIAgent openAIAssistantAgent = await assistantClient.CreateAIAgentAsync(instructions: ParrotInstructions);
```

Additionally for hosted agent providers you can also use the `GetAIAgent` to retrieve an agent from an existing hosted agent.

```csharp
AIAgent azureFoundryAgent = await persistentAgentsClient.GetAIAgentAsync(agentId);
```

### 3. Agent Thread Creation

#### Semantic Kernel

The caller has to know the thread type and create it manually.

```csharp
// Create a thread for the agent conversation.
AgentThread thread = new OpenAIAssistantAgentThread(this.AssistantClient);
AgentThread thread = new AzureAIAgentThread(this.Client);
AgentThread thread = new OpenAIResponseAgentThread(this.Client);
```

#### Agent Framework

The agent is responsible for creating the thread.

```csharp
// New
AgentThread thread = agent.GetNewThread();
```

### 4. Hosted Agent Thread Cleanup

This case applies exclusively to a few AI providers that still provide hosted threads.

#### Semantic Kernel

Threads have a `self` deletion method

i.e: OpenAI Assistants Provider
```csharp
await thread.DeleteAsync();
```

#### Agent Framework 

> [!NOTE]
> OpenAI Responses introduced a new conversation model that simplifies how conversations are handled. This simplifies hosted thread management compared to the now deprecated OpenAI Assistants model. For more information see the [OpenAI Assistants migration guide](https://platform.openai.com/docs/assistants/migration).

Agent Framework doesn't have a thread deletion API in the `AgentThread` type as not all providers support hosted threads or thread deletion and this will become more common as more providers shift to responses based architectures.

If you require thread deletion and the provider allows this, the caller **should** keep track of the created threads and delete them later when necessary via the provider's sdk.

i.e: OpenAI Assistants Provider
```csharp
await assistantClient.DeleteThreadAsync(thread.ConversationId);
```

### 5. Tool Registration

#### Semantic Kernel

In semantic kernel to expose a function as a tool you must:

1. Decorate the function with a `[KernelFunction]` attribute.
2. Have a `Plugin` class or use the `KernelPluginFactory` to wrap the function.
3. Have a `Kernel` to add your plugin to.
4. Pass the `Kernel` to the agent.

```csharp
KernelFunction function = KernelFunctionFactory.CreateFromMethod(GetWeather);
KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("KernelPluginName", [function]);
Kernel kernel = ... // Create kernel
kernel.Plugins.Add(plugin); 

ChatCompletionAgent agent = new() { Kernel = kernel, ... };
```

#### Agent Framework

In agent framework in a single call you can register tools directly in the agent creation process.

```csharp
AIAgent agent = chatClient.CreateAIAgent(tools: [AIFunctionFactory.Create(GetWeather)]);
```

### 6. Agent Non-Streaming Invocation

Key differences can be seen in the method names from `Invoke` to `Run`, return types and parameters `AgentRunOptions`.

#### Semantic Kernel

The Non-Streaming uses a streaming pattern `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>` for returning multiple agent messages.

```csharp
await foreach (AgentResponseItem<ChatMessageContent> result in agent.InvokeAsync(userInput, thread, agentOptions))
{
    Console.WriteLine(result.Message);
}
```

#### Agent Framework

The Non-Streaming returns a single `AgentRunResponse` with the agent response that can contain multiple messages.
The text result of the run is available in `AgentRunResponse.Text` or `AgentRunResponse.ToString()`.
All messages created as part of the response is returned in the `AgentRunResponse.Messages` list.
This may include tool call messages, function results, reasoning updates and final results.

```csharp
AgentRunResponse agentResponse = await agent.RunAsync(userInput, thread);
```

### 7. Agent Streaming Invocation

Key differences in the method names from `Invoke` to `Run`, return types and parameters `AgentRunOptions`.

#### Semantic Kernel

```csharp
await foreach (StreamingChatMessageContent update in agent.InvokeStreamingAsync(userInput, thread))
{
    Console.Write(update);
}
```

#### Agent Framework

Similar streaming API pattern with the key difference being that it returns `AgentRunResponseUpdate` objects including more agent related information per update.

All updates produced by any service underlying the AIAgent is returned. The textual result of the agent is available by concatenating the `AgentRunResponse.Text` values.

```csharp
await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync(userInput, thread))
{
    Console.Write(update); // Update is ToString() friendly
}
```

### 8. Tool Function Signatures

**Problem**: SK plugin methods need `[KernelFunction]` attributes

```csharp
public class MenuPlugin
{
    [KernelFunction] // Required for SK
    public static MenuItem[] GetMenu() => ...;
}
```

**Solution**: AF can use methods directly without attributes

```csharp
public class MenuTools
{
    [Description("Get menu items")] // Optional description
    public static MenuItem[] GetMenu() => ...;
}
```

### 9. Options Configuration

**Problem**: Complex options setup in SK

```csharp
OpenAIPromptExecutionSettings settings = new() { MaxTokens = 1000 };
AgentInvokeOptions options = new() { KernelArguments = new(settings) };
```

**Solution**: Simplified options in AF

```csharp
ChatClientAgentRunOptions options = new(new() { MaxOutputTokens = 1000 });
```

> [!IMPORTANT]
> This example shows passing implementation specific options to a `ChatClientAgent`. Not all `AIAgents` support `ChatClientAgentRunOptions`.
> `ChatClientAgent` is provided to build agents based on underlying inference services, and therefore supports inference options like `MaxOutputTokens`.

### 10. Dependency Injection

#### Semantic Kernel

A `Kernel` registration is required in the service container to be able to create an agent
as every agent abstractions needs to be initialized with a `Kernel` property.

Semantic Kernel uses the `Agent` type as the base abstraction class for agents.

```csharp
services.AddKernel().AddProvider(...);
serviceContainer.AddKeyedSingleton<SemanticKernel.Agents.Agent>(
    TutorName,
    (sp, key) =>
        new ChatCompletionAgent()
        {
            // Passing the kernel is required
            Kernel = sp.GetRequiredService<Kernel>(),
        });
```

### 11. **Agent Type Consolidation**

#### Semantic Kernel

Semantic kernel provides specific agent classes for various services, e.g.

- `ChatCompletionAgent` for use with chat-completion-based inference services.
- `OpenAIAssistantAgent` for use with the OpenAI Assistants service.
- `AzureAIAgent` for use with the Azure AI Foundry Agents service.

#### Agent Framework

The agent framework supports all the abovementioned services via a single agent type, `ChatClientAgent`.

`ChatClientAgent` can be used to build agents using any underlying service that provides an SDK implementing the `Microsoft.Extensions.AI.IChatClient` interface.

#### Agent Framework

The Agent framework provides the `AIAgent` type as the base abstraction class.

```csharp
services.AddKeyedSingleton<AIAgent>(() => client.CreateAIAgent(...));
```

## Migration Samples

This folder contains **separate console application projects** demonstrating how to transition from **Semantic Kernel (SK)** to the new **Agent Framework (AF)**.

Each project shows side-by-side comparisons of equivalent functionality in both frameworks and can be run independently.

Each sample code contains the following:
1. **SK Agent** (Semantic Kernel before)
2. **AF Agent** (Agent Framework after)

### Running the samples from Visual Studio

Open the solution in Visual Studio and set the desired sample project as the startup project. Then, run the project using the built-in debugger or by pressing `F5`.

You will be prompted for any required environment variables if they are not already set.

### Prerequisites

Before you begin, ensure you have the following:

- [.NET 8.0 SDK or later](https://dotnet.microsoft.com/download)
- For Azure AI Foundry samples: Azure OpenAI service endpoint and deployment configured
- For OpenAI samples: OpenAI API key
- For OpenAI Assistants samples: OpenAI API key with Assistant API access

### Environment Variables

Set the appropriate environment variables based on the sample type you want to run:

**For Azure AI Foundry projects:**
```powershell
$env:AZURE_FOUNDRY_PROJECT_ENDPOINT = "https://<your-project>-resource.services.ai.azure.com/api/projects/<your-project>"
```

**For OpenAI and OpenAI Assistants projects:**
```powershell
$env:OPENAI_API_KEY = "sk-..."
```

**For Azure OpenAI and Azure OpenAI Assistants projects:**
```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<your-project>.cognitiveservices.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4o" # Optional, defaults to gpt-4o
```

**Optional debug mode:**
```powershell
$env:AF_SHOW_ALL_DEMO_SETTING_VALUES = "Y"
```

If environment variables are not set, the demos will prompt you to enter values interactively.

### Samples

The migration samples are organized into three categories, each demonstrating different AI service integrations:

|Category|Description|
|---|---|
|[AzureAIFoundry](./AzureAIFoundry/)|Azure OpenAI service integration samples|
|[AzureOpenAI](./AzureOpenAI/)|Direct Azure OpenAI API integration samples|
|[AzureOpenAIAssistants](./AzureOpenAIAssistants/)|Azure OpenAI Assistants API integration samples|
|[AzureOpenAIResponses](./AzureOpenAIResponses/)|Azure OpenAI Responses API integration samples|
|[OpenAI](./OpenAI/)|Direct OpenAI API integration samples|
|[OpenAIAssistants](./OpenAIAssistants/)|OpenAI Assistants API integration samples|
|[OpenAIResponses](./OpenAIResponses/)|OpenAI Responses API integration samples|

## Running the samples from the console

To run any migration sample, navigate to the desired sample directory:

```powershell
# Azure AI Foundry Examples
cd "AzureAIFoundry\Step01_Basics"
dotnet run

# Azure OpenAI Examples
cd "AzureOpenAI\Step01_Basics"
dotnet run

# OpenAI Examples
cd "OpenAI\Step01_Basics"
dotnet run

# OpenAI Assistants Examples
cd "OpenAIAssistants\Step01_Basics"
dotnet run

# OpenAI Responses Examples
cd "OpenAIResponses\Step01_Basics"

# Azure OpenAI Examples
cd "AzureOpenAI\Step01_Basics"
dotnet run

# Azure OpenAI Assistants Examples
cd "AzureOpenAIAssistants\Step01_Basics"
dotnet run
```
