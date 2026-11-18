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
AIAgent openAIAgent = chatClient.AsAIAgent(instructions: ParrotInstructions);
AIAgent azureFoundryAgent = aiProjectClient.AsAIAgent(
    model: deploymentName,
    instructions: ParrotInstructions);
```

When the agent definition must live in the service, as it did for `AzureAIAgent` and the shut-down OpenAI Assistants API, create a Microsoft Foundry Prompt Agent. A Prompt Agent is a versioned agent definition stored in the Foundry project.

```csharp
ProjectsAgentVersion agentVersion = await aiProjectClient.AgentAdministrationClient.CreateAgentVersionAsync(
    agentName,
    new ProjectsAgentVersionCreationOptions(
        new DeclarativeAgentDefinition(model: deploymentName) { Instructions = ParrotInstructions }));
FoundryAgent promptAgent = aiProjectClient.AsAIAgent(agentVersion);
```

For an existing Prompt Agent, retrieve its record by name and adapt that record to `AIAgent`.

```csharp
ProjectsAgentRecord agentRecord =
    await aiProjectClient.AgentAdministrationClient.GetAgentAsync(agentName);
AIAgent azureFoundryAgent = aiProjectClient.AsAIAgent(agentRecord);
```

### 3. Agent Thread Creation

#### Semantic Kernel

The caller has to know the thread type and create it manually.

```csharp
// Create a thread for the agent conversation.
AgentThread thread = new AzureAIAgentThread(this.Client);
AgentThread thread = new OpenAIResponseAgentThread(this.Client);
```

#### Agent Framework

The agent is responsible for creating the session.

```csharp
AgentSession session = await agent.CreateSessionAsync();

// A Foundry Prompt Agent can also create a server-side conversation.
ChatClientAgentSession conversationSession = await promptAgent.CreateConversationSessionAsync();
```

### 4. Hosted Agent Session Cleanup

This case applies exclusively to providers that store conversation state remotely.

#### Semantic Kernel

Threads have a `self` deletion method.

Azure AI Foundry Provider (`AzureAIAgentThread`):
```csharp
await thread.DeleteAsync();
```

#### Agent Framework 

> [!NOTE]
> The OpenAI Assistants API was shut down on August 26, 2026. Migrate Assistants-based agents to Microsoft Foundry Prompt Agents or to OpenAI Responses agents.

Agent Framework doesn't have a session deletion API on `AgentSession` because not all providers support hosted conversation state or deletion.

If deletion is required and the provider supports it, keep track of the created sessions and delete their remote conversation state through the provider SDK.

Microsoft Foundry Prompt Agent:
```csharp
await aiProjectClient.GetProjectOpenAIClient()
    .GetProjectConversationsClient()
    .DeleteConversationAsync(conversationSession.ConversationId);

// Deletes the Prompt Agent and all of its versions.
await aiProjectClient.AgentAdministrationClient.DeleteAgentAsync(agentName);
```

See [AzureAIFoundry/Step05_PromptAgent](./AzureAIFoundry/Step05_PromptAgent/) for the complete lifecycle.

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
AIAgent agent = chatClient.AsAIAgent(tools: [AIFunctionFactory.Create(GetWeather)]);
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

The Non-Streaming returns a single `AgentResponse` that can contain multiple messages.
The text result of the run is available in `AgentResponse.Text` or `AgentResponse.ToString()`.
All messages created as part of the response are returned in the `AgentResponse.Messages` list.
This may include tool call messages, function results, reasoning updates and final results.

```csharp
AgentResponse agentResponse = await agent.RunAsync(userInput, session);
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

The streaming API returns `AgentResponseUpdate` objects that include agent information with each update.

All updates produced by the service underlying the `AIAgent` are returned. The textual result is available by concatenating the `AgentResponseUpdate.Text` values.

```csharp
await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(userInput, session))
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
- `AzureAIAgent` for use with the Azure AI Foundry Agents service.

#### Agent Framework

Agent Framework uses `AIAgent` as the common abstraction across providers.

`ChatClientAgent` builds agents for services that expose the `Microsoft.Extensions.AI.IChatClient` interface. Other providers expose adapters that also return `AIAgent`.

#### Agent Framework

The Agent framework provides the `AIAgent` type as the base abstraction class.

```csharp
services.AddKeyedSingleton<AIAgent>(() => client.AsAIAgent(...));
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

- [.NET 10.0 SDK or later](https://dotnet.microsoft.com/download)
- For Azure AI Foundry samples: Foundry project endpoint and model deployment configured
- For OpenAI samples: OpenAI API key

### Environment Variables

Set the appropriate environment variables based on the sample type you want to run:

**For Azure AI Foundry projects:**
```powershell
$env:AZURE_FOUNDRY_PROJECT_ENDPOINT = "https://<your-project>-resource.services.ai.azure.com/api/projects/<your-project>"
$env:AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME = "gpt-5.4-mini" # Optional, defaults to gpt-5.4-mini
```

**For OpenAI projects:**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-5.6-sol" # Optional, defaults to gpt-5.6-sol
```

**For Azure OpenAI projects:**
```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<your-project>.cognitiveservices.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-5.6-sol" # Optional, defaults to gpt-5.6-sol
```

The reasoning-model, agent orchestration, and OpenAPI tool-call samples default to `gpt-5.6-terra`. The Azure AI Foundry samples default to `gpt-5.4-mini`, because the classic Foundry Agents service used by the Semantic Kernel `AzureAIAgent` rejects the `top_p` parameter it sends to GPT-5.6 models. If you use a different model, confirm it isn't deprecated in the [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations) list or the [Microsoft Foundry model retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule).

**Optional debug mode:**
```powershell
$env:AF_SHOW_ALL_DEMO_SETTING_VALUES = "Y"
```

If environment variables are not set, the demos will prompt you to enter values interactively.

### Samples

The migration samples are organized into different categories, each demonstrating different AI service integrations and orchestration patterns:

|Category|Description|
|---|---|
|[AzureAIFoundry](./AzureAIFoundry/)|Microsoft Foundry project integration samples, including a Prompt Agent lifecycle migration in Step05|
|[AzureOpenAI](./AzureOpenAI/)|Direct Azure OpenAI API integration samples|
|[AzureOpenAIResponses](./AzureOpenAIResponses/)|Azure OpenAI Responses API integration samples|
|[OpenAI](./OpenAI/)|Direct OpenAI API integration samples|
|[OpenAIResponses](./OpenAIResponses/)|OpenAI Responses API integration samples|
|[AgentOrchestrations](./AgentOrchestrations/)|Agent orchestration patterns including concurrent, sequential, and handoff workflows|

## Running the samples from the console

To run any migration sample, navigate to the desired sample directory:

```powershell
# Azure AI Foundry Examples
cd "AzureAIFoundry\Step01_Basics"
dotnet run

# Azure AI Foundry Prompt Agent (replaces OpenAI Assistants and server-side AzureAIAgent definitions)
cd "AzureAIFoundry\Step05_PromptAgent"
dotnet run

# Azure OpenAI Examples
cd "AzureOpenAI\Step01_Basics"
dotnet run

# Azure OpenAI Responses Examples
cd "AzureOpenAIResponses\Step01_Basics"
dotnet run

# OpenAI Examples
cd "OpenAI\Step01_Basics"
dotnet run

# OpenAI Responses Examples
cd "OpenAIResponses\Step01_Basics"
dotnet run

# Agent Orchestrations Examples
cd "AgentOrchestrations\Step01_Concurrent"
dotnet run

cd "AgentOrchestrations\Step02_Sequential"
dotnet run

cd "AgentOrchestrations\Step03_Handoff"
dotnet run
```
