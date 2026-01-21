# Instructions for migrating from Semantic Kernel Agents to Agent Framework in .NET projects.

## Scope

When you are asked to migrate a project from `Microsoft.SemanticKernel.Agents` to `Microsoft.Agents.AI` you need to determine for which projects you need to do it.
If a single project is specified - do it for that project only. If you are asked to do it for a solution, migrate all projects in the solution
that reference `Microsoft.SemanticKernel.Agents` or related Semantic Kernel agent packages. If you don't know which projects to migrate, ask the user.

## Things to consider while doing migration

- NuGet package names, assembly names, projects names or other dependencies names are case insensitive(!). You ***must take it into account*** when doing something
  with project dependencies, like searching for dependencies or when removing them from projects etc.
- Agent Framework uses different namespace patterns and API structures compared to Semantic Kernel Agents
- Text-based heuristics should be avoided in favor of proper content type inspection when available.

## Planning

For each project that needs to be migrated, you need to do the following:

<agent_type_identification>
- Find projects depending on `Microsoft.SemanticKernel.Agents` or related Semantic Kernel agent packages (when searching for projects, if some projects are not part of the
  solution or you could not find the project, notify user and continue with other projects).
- Identify the specific Semantic Kernel agent types being used:
  - `ChatCompletionAgent` → `ChatClientAgent`
  - `OpenAIAssistantAgent` → `assistantsClient.CreateAIAgent()` (via OpenAI Assistants client extension)
  - `AzureAIAgent` → `persistentAgentsClient.CreateAIAgent()` (via Azure AI Foundry client extension)
  - `OpenAIResponseAgent` → `responsesClient.CreateAIAgent()` (via OpenAI Responses client extension)
  - `A2AAgent` → `AIAgent` (via A2A card resolver)
  - `BedrockAgent` → Custom implementation required (not supported)
- Determine if agents are being created new or retrieved from hosted services:
  - **New agents**: Use `CreateAIAgent()` methods
  - **Existing hosted agents**: Use `GetAIAgent(agentId)` methods for OpenAI Assistants and Azure AI Foundry
</agent_type_identification>

- Determine the AI provider being used (OpenAI, Azure OpenAI, Azure AI Foundry, etc.)
- Analyze tool/function registration patterns
- Review thread management and invocation patterns

## Execution

***Important***: when running steps in this section you must not pause, you must continue until you are done with all steps or you are truly unable to
continue and need user's interaction (you will be penalized if you stop unnecessarily).

Keep in mind information in the next section about differences and follow these steps in the order they are specified (you will be penalized if you do steps
below in wrong order or skip any of them):

1. For each project that has an explicit package dependency to Semantic Kernel agent packages in the project file or some imported MSBuild targets (some
   project could receive package dependencies transitively, so avoid adding new package dependencies for such projects), do the following:

- Remove the Semantic Kernel agent package references from the project file:
  - `Microsoft.SemanticKernel.Agents.Core`
  - `Microsoft.SemanticKernel.Agents.OpenAI`
  - `Microsoft.SemanticKernel.Agents.AzureAI`
  - `Microsoft.SemanticKernel` (if only used for agents)
- Add the appropriate Agent Framework package references based on the provider being used:
  - `Microsoft.Agents.AI.Abstractions` (always required)
  - `Microsoft.Agents.AI.OpenAI` (for OpenAI and Azure OpenAI providers)
  - For unsupported providers (Bedrock, CopilotStudio), note in the report that custom implementation is required
- If projects use Central Package Management, update the `Directory.Packages.props` file to remove the Semantic Kernel agent package versions in addition to
  removing package reference from projects.
  When adding the Agent Framework PackageReferences, add them to affected project files without a version and add PackageVersion elements to the
  Directory.Packages.props file with the version that supports the project's target framework.

2. Update code files using Semantic Kernel Agents in the selected projects (and in projects that depend on them since they could receive Semantic Kernel transitively):

- Find ***all*** code files in the selected projects (and in projects that depend on them since they could receive Semantic Kernel transitively).
  When doing search of code files that need changes, prefer calling search tools with `upgrade_` prefix if available. Also do pass project's root folder for all
  selected projects or projects that depend on them.
- Update the code files that use Semantic Kernel Agents to use Agent Framework instead. You never should add placeholders when updating code, or remove any comments in the code files,
  you must keep the business logic as close as possible to the original code but use new API. When checking if code file needs to be updated, you should check for
  using statements, types and API from `Microsoft.SemanticKernel.Agents` namespace (skip comments and string literal constants).
- Ensure that you replace all Semantic Kernel agent using statements with Agent Framework using statements (always check if there are any other Semantic Kernel agent
  API used in the file having any of the Semantic Kernel agent using statements; if no other API detected, Semantic Kernel agent using statements should be just removed
  instead of replaced). If there were no Semantic Kernel agent using statements in the file, do not add Agent Framework using statements.
- When replacing types you must ensure that you add using statements for them, since some types that lived in main `Microsoft.SemanticKernel.Agents` namespace live in other namespaces
  under `Microsoft.Agents.AI`. For example, `Microsoft.SemanticKernel.Agents.ChatCompletionAgent` is replaced with `Microsoft.Agents.AI.ChatClientAgent`, when that
  happens using statement with `Microsoft.Agents.AI` needs to be added (unless you use fully qualified type name)
- If you see some code that really cannot be converted or will have potential behavior changes at runtime, remember files and code lines where it
  happens at the end of the migration process you will generate a report markdown file and list all follow up steps user would have to do.

3. Validate that all places where Semantic Kernel Agents were used are migrated. To do that search for `Microsoft.SemanticKernel.Agents` in all affected projects and projects that depend
   on them again and if still see any Semantic Kernel agent presence go back to step 2. Steps 2 and 3 should be repeated until you see no Semantic Kernel agent references.

4. Build all modified projects to ensure that they compile without errors. If there are any build errors, you must fix them all yourself one by one and
   don't stop until all errors are fixed without breaking any of the migration guidance.

5. **Validate Migration**: Use the validation checklist below to ensure complete migration.

6. Generate the report file under `<solution root>\.github folder`, the file name should be `SemanticKernelToAgentFrameworkReport.md`, it is highly important that
   you generate report when migration complete. Report should contain:
     - all project dependencies changes (mention what was changed, added or removed, including provider-specific packages)
     - all code files that were changed (mention what was changed in the file, if it was not changed, just mention that the file was not changed)
     - provider-specific migration patterns used (OpenAI, Azure OpenAI, Azure AI Foundry, A2A, ONNX, etc.)
     - all cases where you could not convert the code because of unsupported features and you were unable to find a workaround
     - unsupported providers that require custom implementation (Bedrock, CopilotStudio)
     - breaking glass pattern migrations (InnerContent → RawRepresentation) and any CodeInterpreter or advanced tool usage
     - all behavioral changes that have to be verified at runtime
     - provider-specific configuration changes that may affect behavior
     - all follow up steps that user would have to do in the report markdown file

## Migration Validation Checklist

After completing migration, verify these specific items:

1. **Compilation**: Execute `dotnet build` on all modified projects - zero errors required
2. **Namespace Updates**: Confirm all `using Microsoft.SemanticKernel.Agents` statements are replaced
3. **Method Calls**: Verify all `InvokeAsync` calls are changed to `RunAsync`
4. **Return Types**: Confirm handling of `AgentRunResponse` instead of `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>`
5. **Thread Creation**: Validate all thread creation uses `agent.GetNewThread()` pattern
6. **Tool Registration**: Ensure `[KernelFunction]` attributes are removed and `AIFunctionFactory.Create()` is used
7. **Options Configuration**: Verify `AgentRunOptions` or `ChatClientAgentRunOptions` replaces `AgentInvokeOptions`
8. **Breaking Glass**: Test `RawRepresentation` access replaces `InnerContent` access

## Detailed information about differences in Semantic Kernel Agents and Agent Framework

<api_changes>
Agent Framework provides functionality for creating and managing AI agents through the Microsoft.Extensions.AI package ecosystem. The framework uses different APIs and patterns compared to Semantic Kernel Agents.

Key API differences:
- Agent creation: Remove Kernel dependency, use direct client-based creation
- Method names: `InvokeAsync` → `RunAsync`, `InvokeStreamingAsync` → `RunStreamingAsync`
- Return types: `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>` → `AgentRunResponse`
- Thread creation: Provider-specific constructors → `agent.GetNewThread()`
- Tool registration: `KernelPlugin` system → Direct `AIFunction` registration
- Options: `AgentInvokeOptions` → Provider-specific run options (e.g., `ChatClientAgentRunOptions`)
</api_changes>

<configuration_changes>
Configuration patterns have changed from Kernel-based to direct client configuration:
- Remove `Kernel.CreateBuilder()` patterns
- Replace with provider-specific client creation
- Update namespace imports from `Microsoft.SemanticKernel.Agents` to `Microsoft.Agents.AI`
- Change tool registration from attribute-based to factory-based
</configuration_changes>

### Exact API Mappings

<agent_type_identification>
Replace these Semantic Kernel agent classes with their Agent Framework equivalents:

| Semantic Kernel Class | Agent Framework Replacement | Constructor Changes |
|----------------------|----------------------------|-------------------|
| `IChatCompletionService` | `IChatClient` | Convert to `IChatClient` using `chatService.AsChatClient()` extensions |
| `ChatCompletionAgent` | `ChatClientAgent` | Remove `Kernel` parameter, add `IChatClient` parameter |
| `OpenAIAssistantAgent` | `AIAgent` (via extension) | **New**: `OpenAIClient.GetAssistantClient().CreateAIAgent()` <br> **Existing**: `OpenAIClient.GetAssistantClient().GetAIAgent(assistantId)` |
| `AzureAIAgent` | `AIAgent` (via extension) | **New**: `PersistentAgentsClient.CreateAIAgent()` <br> **Existing**: `PersistentAgentsClient.GetAIAgent(agentId)` |
| `OpenAIResponseAgent` | `AIAgent` (via extension) | Replace with `OpenAIClient.GetOpenAIResponseClient().CreateAIAgent()` |
| `A2AAgent` | `AIAgent` (via extension) | Replace with `A2ACardResolver.GetAIAgentAsync()` |
| `BedrockAgent` | Not supported | Custom implementation required |

**Important distinction:**
- **CreateAIAgent()**: Use when creating new agents in the hosted service
- **GetAIAgent(agentId)**: Use when retrieving existing agents from the hosted service
</agent_type_identification>

<api_changes>
Replace these method calls:

| Semantic Kernel Method | Agent Framework Method | Parameter Changes |
|----------------------|----------------------|------------------|
| `agent.InvokeAsync(message, thread, options)` | `agent.RunAsync(message, thread, options)` | Same parameters, different return type |
| `agent.InvokeStreamingAsync(message, thread, options)` | `agent.RunStreamingAsync(message, thread, options)` | Same parameters, different return type |
| `new ChatHistoryAgentThread()` | `agent.GetNewThread()` | No parameters needed |
| `new OpenAIAssistantAgentThread(client)` | `agent.GetNewThread()` | No parameters needed |
| `new AzureAIAgentThread(client)` | `agent.GetNewThread()` | No parameters needed |
| `thread.DeleteAsync()` | Provider-specific cleanup | Use provider client directly |

Return type changes:
- `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>` → `AgentRunResponse`
- `IAsyncEnumerable<StreamingChatMessageContent>` → `IAsyncEnumerable<AgentRunResponseUpdate>`
</api_changes>

<configuration_changes>
Replace these configuration patterns:

| Semantic Kernel Pattern | Agent Framework Pattern |
|------------------------|------------------------|
| `AgentInvokeOptions` | `AgentRunOptions` <br> **ChatClientAgent**: `ChatClientAgentRunOptions` |
| `KernelArguments` | If no arguments are provided, do nothing. If arguments are provided, template is not supported and the prompt must be rendered before calling agent |
| `[KernelFunction]` attribute | Remove attribute, use `AIFunctionFactory.Create()` |
| `KernelPlugin` registration | Direct function list in agent creation |
| `InnerContent` property | `RawRepresentation` property |
| `content.Metadata` property | `AdditionalProperties` property |
</configuration_changes>

<behavioral_changes>
### Functional Differences

Agent Framework changes these behaviors compared to Semantic Kernel Agents:

1. **Thread Management**: Agent Framework automatically manages thread state. Semantic Kernel required manual thread updates in some scenarios (e.g., OpenAI Responses).

2. **Return Types**:
   - Non-streaming: Returns single `AgentRunResponse` instead of `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>`
   - Streaming: Returns `IAsyncEnumerable<AgentRunResponseUpdate>` instead of `IAsyncEnumerable<StreamingChatMessageContent>`

3. **Tool Registration**: Agent Framework uses direct function registration without requiring `[KernelFunction]` attributes.

4. **Usage Metadata**: Agent Framework provides unified `UsageDetails` access via `response.Usage` and `update.Contents.OfType<UsageContent>()`.

5. **Breaking Glass**: Access underlying SDK objects via `RawRepresentation` instead of `InnerContent`.
</behavioral_changes>

### Namespace Updates

<configuration_changes>
Replace these exact namespace imports:

**Remove these Semantic Kernel namespaces:**
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.Connectors.OpenAI;
```

**Add these Agent Framework namespaces:**
```csharp
using Microsoft.Extensions.AI;
using Microsoft.Agents.AI;
// Provider-specific namespaces (add only if needed):
using OpenAI; // For OpenAI provider
using Azure.AI.OpenAI; // For Azure OpenAI provider
using Azure.AI.Agents.Persistent; // For Azure AI Foundry provider
using Azure.Identity; // For Azure authentication
```
</configuration_changes>

### Chat Completion Abstractions

<configuration_changes>

**Replace this Semantic Kernel pattern:**
```csharp
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(modelId, apiKey)
    .Build();

ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};
```

**With this Agent Framework pattern:**
```csharp
// Method 1: Direct constructor
IChatClient chatClient = new OpenAIClient(apiKey).GetChatClient(modelId).AsIChatClient();
AIAgent agent = new ChatClientAgent(chatClient, instructions: "You are a helpful assistant");

// Method 2: Extension method (recommended)
AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: "You are a helpful assistant");
```
</configuration_changes>

### Chat Completion Service

<configuration_changes>

**Replace this Semantic Kernel pattern:**

```csharp
IChatCompletionService completionService = kernel.GetService<IChatCompletionService>();

ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};
```

**With this Agent Framework pattern:**

Agent Framework does not support `IChatCompletionService` directly. Instead, use `IChatClient` as the common abstraction
converting from `IChatCompletionService` to `IChatClient` via `AsChatClient()` extension method or creating a new `IChatClient`
 instance directly using the provider package dedicated extensions.

```csharp
IChatCompletionService completionService = kernel.GetService<IChatCompletionService>();
IChatClient chatClient = completionService.AsChatClient();

var agent = new ChatClientAgent(chatClient, instructions: "You are a helpful assistant");
```
</configuration_changes>

### Agent Creation Transformation

<configuration_changes>

**Replace this Semantic Kernel pattern:**
```csharp
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatClient(modelId, apiKey)
    .Build();

ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};
```

**With this Agent Framework pattern:**
```csharp
// Method 1: Direct constructor (OpenAI/AzureOpenAI Package specific)
IChatClient chatClient = new OpenAIClient(apiKey).GetChatClient(modelId).AsIChatClient();
AIAgent agent = new ChatClientAgent(chatClient, instructions: "You are a helpful assistant");

// Method 2: Extension method (recommended)
AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: "You are a helpful assistant");
```

**Required changes:**
1. Remove `Kernel.CreateBuilder()` and `.Build()` calls
2. Replace `ChatCompletionAgent` with `ChatClientAgent` or use extension methods
3. Remove `Kernel` property assignment
4. Pass `IChatClient` directly to constructor or use extension methods
</configuration_changes>

### Thread Management Transformation

<api_changes>
**Replace these Semantic Kernel thread creation patterns:**
```csharp
// Remove these provider-specific thread constructors:
AgentThread thread = new ChatHistoryAgentThread();
AgentThread thread = new OpenAIAssistantAgentThread(assistantClient);
AgentThread thread = new AzureAIAgentThread(azureClient);
```

**With this unified Agent Framework pattern:**
```csharp
// Use this single pattern for all agent types:
AgentThread thread = agent.GetNewThread();
```

**Required changes:**
1. Remove all `new [Provider]AgentThread()` constructor calls
2. Replace with `agent.GetNewThread()` method call
3. Remove provider client parameters from thread creation
4. Use the same pattern regardless of agent provider type
</api_changes>

### Tool Registration Transformation

<configuration_changes>
**Replace this Semantic Kernel tool registration pattern:**
```csharp
[KernelFunction] // Remove this attribute
[Description("Get the weather for a location")]
static string GetWeather(string location) => $"Weather in {location}";

KernelFunction kernelFunction = KernelFunctionFactory.CreateFromMethod(GetWeather);
KernelPlugin kernelPlugin = KernelPluginFactory.CreateFromFunctions("WeatherPlugin", [kernelFunction]);
kernel.Plugins.Add(kernelPlugin);

ChatCompletionAgent agent = new() { Kernel = kernel };
```

**With this Agent Framework pattern:**
```csharp
[Description("Get the weather for a location")] // Keep Description attribute
static string GetWeather(string location) => $"Weather in {location}";

AIAgent agent = chatClient.CreateAIAgent(
    instructions: "You are a helpful assistant",
    tools: [AIFunctionFactory.Create(GetWeather)]);
```

**Required changes:**
1. Remove `[KernelFunction]` attributes from methods
2. Keep `[Description]` attributes for function descriptions
3. Remove `KernelFunctionFactory.CreateFromMethod()` calls
4. Remove `KernelPluginFactory.CreateFromFunctions()` calls
5. Remove `kernel.Plugins.Add()` calls
6. Replace with `AIFunctionFactory.Create()` in tools parameter
7. Pass tools directly to agent creation method
</configuration_changes>

### Runtime Tool Registration Transformation

<configuration_changes>
In Semantic Kernel, plugins/tools could be registered via DI and then added to the kernel at runtime. Agent Framework requires tools to be provided either at agent creation time or at runtime via options.

**Replace this Semantic Kernel runtime tool registration pattern:**
```csharp
// Semantic Kernel - Tools registered via DI and added to kernel instance
IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
kernelBuilder.Services.AddSingleton<ISearchService, SearchService>();
kernelBuilder.Plugins.AddFromType<SearchPlugin>();

Kernel kernel = kernelBuilder.Build();
ChatCompletionAgent agent = new() { Kernel = kernel };

// Tools are available on every invocation
await foreach (var item in agent.InvokeAsync(userInput, thread)) { ... }
```

**With this Agent Framework pattern using runtime tool registration:**
```csharp
// Define the tool function
[Description("Get the weather for a location")]
static string GetWeather(string location) => $"Weather in {location}: Sunny";

// Create agent without tools
AIAgent agent = chatClient.CreateAIAgent(
    instructions: "You are a helpful assistant");

// Provide tools at runtime via ChatClientAgentRunOptions
var chatOptions = new ChatOptions 
{ 
    Tools = [AIFunctionFactory.Create(GetWeather)] 
};
var options = new ChatClientAgentRunOptions(chatOptions);

AgentRunResponse result = await agent.RunAsync(userInput, thread, options);
```

**Required changes:**
1. Create agent without tools if tools need to be determined at runtime
2. Create `ChatOptions` with the `Tools` property containing the tools
3. Wrap `ChatOptions` in `ChatClientAgentRunOptions`
4. Pass options to `RunAsync()` or `RunStreamingAsync()` methods

**Note:** This pattern is useful for scenarios where tools need to be:
- Enabled/disabled per user or per request
- Added based on tenant configuration, licensing, or feature flags
- Composed dynamically in modular systems
</configuration_changes>

### Invocation Method Transformation

<api_changes>
**Replace this Semantic Kernel non-streaming pattern:**
```csharp
await foreach (AgentResponseItem<ChatMessageContent> item in agent.InvokeAsync(userInput, thread, options))
{
    Console.WriteLine(item.Message);
}
```

**With this Agent Framework non-streaming pattern:**
```csharp
AgentRunResponse result = await agent.RunAsync(userInput, thread, options);
Console.WriteLine(result);
```

**Replace this Semantic Kernel streaming pattern:**
```csharp
await foreach (StreamingChatMessageContent update in agent.InvokeStreamingAsync(userInput, thread, options))
{
    Console.Write(update.Message);
}
```

**With this Agent Framework streaming pattern:**
```csharp
await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync(userInput, thread, options))
{
    Console.Write(update);
}
```

**Required changes:**
1. Replace `agent.InvokeAsync()` with `agent.RunAsync()`
2. Replace `agent.InvokeStreamingAsync()` with `agent.RunStreamingAsync()`
3. Change return type handling from `IAsyncEnumerable<AgentResponseItem<ChatMessageContent>>` to `AgentRunResponse`
4. Change streaming type from `StreamingChatMessageContent` to `AgentRunResponseUpdate`
5. Remove `await foreach` for non-streaming calls
6. Access message content directly from result object instead of iterating
</api_changes>

### Options and Configuration Transformation

<configuration_changes>
**Replace this Semantic Kernel options pattern:**
```csharp
OpenAIPromptExecutionSettings settings = new() { MaxTokens = 1000 };
AgentInvokeOptions options = new() { KernelArguments = new(settings) };
```

**With this Agent Framework options pattern:**
```csharp
ChatClientAgentRunOptions options = new(new ChatOptions { MaxOutputTokens = 1000 });
```

**Required changes:**
1. Remove `OpenAIPromptExecutionSettings` (or other provider-specific settings)
2. Remove `AgentInvokeOptions` wrapper
3. Remove `KernelArguments` wrapper
4. Replace with `ChatClientAgentRunOptions` containing `ChatOptions`
5. Update property names: `MaxTokens` → `MaxOutputTokens`
6. Pass options directly to `RunAsync()` or `RunStreamingAsync()` methods
</configuration_changes>

### Dependency Injection Transformation

<configuration_changes>
**Replace this Semantic Kernel DI pattern:**

Different providers require different kernel extensions:

```csharp
services.AddKernel().AddOpenAIChatClient(modelId, apiKey);
services.AddTransient<ChatCompletionAgent>(sp => new()
{
    Kernel = sp.GetRequiredService<Kernel>(),
    Instructions = "You are helpful"
});
```

**With this Agent Framework DI pattern:**
```csharp
services.AddTransient<AIAgent>(sp =>
    new OpenAIClient(apiKey)
        .GetChatClient(modelId)
        .CreateAIAgent(instructions: "You are helpful"));
```

**Required changes:**
1. Remove `services.AddKernel()` registration
2. Remove provider-specific kernel extensions (e.g., `.AddOpenAIChatClient()`)
3. Replace `ChatCompletionAgent` with `AIAgent` in service registration
4. Remove `Kernel` dependency from constructor
5. Use direct client creation and extension methods
6. Remove `sp.GetRequiredService<Kernel>()` calls
</configuration_changes>

### Thread Cleanup Transformation

<api_changes>
**Replace this Semantic Kernel cleanup pattern:**
```csharp
await thread.DeleteAsync(); // For hosted threads
```

**With these Agent Framework cleanup patterns:**

For every thread created if there's intent to cleanup, the caller should track all the created threads for the provider that support hosted threads for cleanup purposes.

```csharp
// For OpenAI Assistants (when cleanup is needed):
var assistantClient = new OpenAIClient(apiKey).GetAssistantClient();
await assistantClient.DeleteThreadAsync(thread.ConversationId);

// For Azure AI Foundry (when cleanup is needed):
var persistentClient = new PersistentAgentsClient(endpoint, credential);
await persistentClient.Threads.DeleteThreadAsync(thread.ConversationId);

// No thread and agent cleanup is needed for non-hosted agent providers like 
// - Azure OpenAI Chat Completion
// - OpenAI Chat Completion
// - Azure OpenAI Responses
// - OpenAI Responses
```

**Required changes:**
1. Remove `thread.DeleteAsync()` calls
2. Use provider-specific client for cleanup when required
3. Access thread ID via `thread.ConversationId` property
4. Only implement cleanup for providers that require it (Assistants, Azure AI Foundry)
</api_changes>

### Provider-Specific Creation Patterns

<configuration_changes>
Use these exact patterns for each provider:

**OpenAI Chat Completion:**
```csharp
AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: instructions);
```

**OpenAI Assistants (New):**
```csharp
AIAgent agent = new OpenAIClient(apiKey)
    .GetAssistantClient()
    .CreateAIAgent(modelId, instructions: instructions);
```

**OpenAI Assistants (Existing):**
```csharp
AIAgent agent = new OpenAIClient(apiKey)
    .GetAssistantClient()
    .GetAIAgent(assistantId);
```

**Azure OpenAI:**
```csharp
AIAgent agent = new AzureOpenAIClient(endpoint, credential)
    .GetChatClient(deploymentName)
    .CreateAIAgent(instructions: instructions);
```

**Azure AI Foundry (New):**
```csharp
AIAgent agent = new PersistentAgentsClient(endpoint, credential)
    .CreateAIAgent(model: deploymentName, instructions: instructions);
```

**Azure AI Foundry (Existing):**
```csharp
AIAgent agent = await new PersistentAgentsClient(endpoint, credential)
    .GetAIAgentAsync(agentId);
```

**A2A:**
```csharp
A2ACardResolver resolver = new(new Uri(agentHost));
AIAgent agent = await resolver.GetAIAgentAsync();
```
</configuration_changes>

### Complete Migration Examples

#### Basic Agent Creation Transformation
<configuration_changes>
**Replace this complete Semantic Kernel pattern:**
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatClient(modelId, apiKey)
    .Build();

ChatCompletionAgent agent = new()
{
    Instructions = "You are helpful",
    Kernel = kernel
};

AgentThread thread = new ChatHistoryAgentThread();
```

**With this complete Agent Framework pattern:**
```csharp
using Microsoft.Agents.AI;
using OpenAI;

AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: "You are helpful");

AgentThread thread = agent.GetNewThread();
```
</configuration_changes>

#### Tool Registration Transformation
<configuration_changes>
**Replace this complete Semantic Kernel tool pattern:**
```csharp
[KernelFunction] // Remove this attribute
[Description("Get weather information")]
static string GetWeather([Description("Location")] string location)
    => $"Weather in {location}";

KernelFunction function = KernelFunctionFactory.CreateFromMethod(GetWeather);
KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Weather", [function]);
kernel.Plugins.Add(plugin);
```

**With this complete Agent Framework tool pattern:**
```csharp
[Description("Get weather information")] // Keep this attribute
static string GetWeather([Description("Location")] string location)
    => $"Weather in {location}";

AIAgent agent = chatClient.CreateAIAgent(
    instructions: "You are a helpful assistant",
    tools: [AIFunctionFactory.Create(GetWeather)]);
```
</configuration_changes>

#### Agent Invocation Transformation
<api_changes>
**Replace this complete Semantic Kernel invocation pattern:**
```csharp
OpenAIPromptExecutionSettings settings = new() { MaxTokens = 1000 };
AgentInvokeOptions options = new() { KernelArguments = new(settings) };

await foreach (var result in agent.InvokeAsync(input, thread, options))
{
    Console.WriteLine(result.Message);
}
```

**With this complete Agent Framework invocation pattern:**
```csharp
ChatClientAgentRunOptions options = new(new ChatOptions { MaxOutputTokens = 1000 });

AgentRunResponse result = await agent.RunAsync(input, thread, options);
Console.WriteLine(result);

// Access underlying content when needed:
var chatResponse = result.RawRepresentation as ChatResponse;
// Access underlying SDK objects via chatResponse?.RawRepresentation
```
</api_changes>

### Usage Metadata Transformation

<api_changes>
**Replace this Semantic Kernel non-streaming usage pattern:**
```csharp
await foreach (var result in agent.InvokeAsync(input, thread, options))
{
    if (result.Message.Metadata?.TryGetValue("Usage", out object? usage) ?? false)
    {
        if (usage is ChatTokenUsage openAIUsage)
        {
            Console.WriteLine($"Tokens: {openAIUsage.TotalTokenCount}");
        }
    }
}
```

**With this Agent Framework non-streaming usage pattern:**
```csharp
AgentRunResponse result = await agent.RunAsync(input, thread, options);
Console.WriteLine($"Tokens: {result.Usage.TotalTokenCount}");
```

**Replace this Semantic Kernel streaming usage pattern:**
```csharp
await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(message, agentThread))
{
    if (response.Metadata?.TryGetValue("Usage", out object? usage) ?? false)
    {
        if (usage is ChatTokenUsage openAIUsage)
        {
            Console.WriteLine($"Tokens: {openAIUsage.TotalTokenCount}");
        }
    }
}
```

**With this Agent Framework streaming usage pattern:**
```csharp
await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync(input, thread, options))
{
    if (update.Contents.OfType<UsageContent>().FirstOrDefault() is { } usageContent)
    {
        Console.WriteLine($"Tokens: {usageContent.Details.TotalTokenCount}");
    }
}
```
</api_changes>



### Breaking Glass Pattern Transformation

<api_changes>
**Replace this Semantic Kernel breaking glass pattern:**
```csharp
await foreach (var content in agent.InvokeAsync(userInput, thread))
{
    UnderlyingSdkType? underlyingChatMessage = content.Message.InnerContent as UnderlyingSdkType;
}
```

**With this Agent Framework breaking glass pattern:**
```csharp
var agentRunResponse = await agent.RunAsync(userInput, thread);

// If the agent uses a ChatClient the first breaking glass probably will be a Microsoft.Extensions.AI.ChatResponse
ChatResponse? chatResponse = agentRunResponse.RawRepresentation as ChatResponse;

// If thats the case, to access the underlying SDK types you will need to break glass again.
UnderlyingSdkType? underlyingChatMessage = chatResponse?.RawRepresentation as UnderlyingSdkType;
```

**Required changes:**
1. Replace `InnerContent` property access with `RawRepresentation` property access
2. Cast `RawRepresentation` to appropriate type expected
3. If the `RawRepresentation` is a `Microsoft.Extensions.AI` type, break glass again to access the underlying SDK types
</api_changes>

#### CodeInterpreter Tool Transformation

<behavioral_changes>
**Replace this Semantic Kernel CodeInterpreter pattern:**
```csharp
await foreach (var content in agent.InvokeAsync(userInput, thread))
{
    bool isCode = content.Message.Metadata?.ContainsKey(AzureAIAgent.CodeInterpreterMetadataKey) ?? false;
    Console.WriteLine($"# {content.Message.Role}{(isCode ? "\n# Generated Code:\n" : ":")}{content.Message.Content}");

    // Process annotations
    foreach (var item in content.Message.Items)
    {
        if (item is AnnotationContent annotation)
        {
            Console.WriteLine($"[{item.GetType().Name}] {annotation.Label}: File #{annotation.ReferenceId}");
        }
        else if (item is FileReferenceContent fileReference)
        {
            Console.WriteLine($"[{item.GetType().Name}] File #{fileReference.FileId}");
        }
    }
}
```

**With this Agent Framework CodeInterpreter pattern:**
```csharp
var result = await agent.RunAsync(userInput, thread);
Console.WriteLine(result);

// Extract chat response MEAI type via first level breaking glass
var chatResponse = result.RawRepresentation as ChatResponse;

// Extract underlying SDK updates via second level breaking glass
var underlyingStreamingUpdates = chatResponse?.RawRepresentation as IEnumerable<object?> ?? [];

StringBuilder generatedCode = new();
foreach (object? underlyingUpdate in underlyingStreamingUpdates ?? [])
{
    if (underlyingUpdate is RunStepDetailsUpdate stepDetailsUpdate && stepDetailsUpdate.CodeInterpreterInput is not null)
    {
        generatedCode.Append(stepDetailsUpdate.CodeInterpreterInput);
    }
}

if (!string.IsNullOrEmpty(generatedCode.ToString()))
{
    Console.WriteLine($"\n# {chatResponse?.Messages[0].Role}:Generated Code:\n{generatedCode}");
}
```

**Functional differences:**
1. Code interpreter output is separate from text content, not a metadata property
2. Access code via `RunStepDetailsUpdate.CodeInterpreterInput` instead of metadata
3. Use breaking glass pattern to access underlying SDK objects
4. Process text content and code interpreter output independently
</behavioral_changes>

#### Provider-Specific Options Configuration

<configuration_changes>
For advanced model settings not available in `ChatOptions`, use the `RawRepresentationFactory` property:

```csharp
var agentOptions = new ChatClientAgentRunOptions(new ChatOptions
{
    MaxOutputTokens = 8000,
    // Breaking glass to access provider-specific options
    RawRepresentationFactory = (_) => new OpenAI.Responses.ResponseCreationOptions()
    {
        ReasoningOptions = new()
        {
            ReasoningEffortLevel = OpenAI.Responses.ResponseReasoningEffortLevel.High,
            ReasoningSummaryVerbosity = OpenAI.Responses.ResponseReasoningSummaryVerbosity.Detailed
        }
    }
});
```

**Use this pattern when:**
1. Standard `ChatOptions` properties don't cover required model settings
2. Provider-specific configuration is needed (e.g., reasoning effort level)
3. Advanced SDK features need to be accessed
</configuration_changes>

#### Type-Safe Extension Methods

<api_changes>
Use provider-specific extension methods for safer breaking glass access:

```csharp
using OpenAI; // Brings in extension methods

// Type-safe extraction of OpenAI ChatCompletion
var chatCompletion = result.AsChatCompletion();

// Access underlying OpenAI objects safely
var openAIResponse = chatCompletion.GetRawResponse();
```

**Available extension methods:**
- `result.AsChatCompletion()` for OpenAI providers
- `result.GetRawResponse()` for accessing underlying SDK responses
- Provider-specific extensions for type-safe casting
</api_changes>



### Common Migration Issues and Solutions

<configuration_changes>
**Issue: Missing Using Statements**
- **Problem**: Compilation errors due to missing namespace imports
- **Solution**: Add `using Microsoft.Agents.AI;` and remove `using Microsoft.SemanticKernel.Agents;`

**Issue: Tool Function Signatures**
- **Problem**: `[KernelFunction]` attributes cause compilation errors
- **Solution**: Remove `[KernelFunction]` attributes, keep `[Description]` attributes

**Issue: Thread Type Mismatches**
- **Problem**: Provider-specific thread constructors not found
- **Solution**: Replace all thread constructors with `agent.GetNewThread()`

**Issue: Options Configuration**
- **Problem**: `AgentInvokeOptions` type not found
- **Solution**: Replace with `AgentRunOptions` or `ChatClientAgentRunOptions` containing `ChatOptions`

**Issue: Dependency Injection**
- **Problem**: `Kernel` service registration not found
- **Solution**: Remove `services.AddKernel()`, use direct client registration
</configuration_changes>

### Migration Execution Steps

<configuration_changes>
1. **Update Package References**: Remove SK packages, add AF packages per provider
2. **Update Namespaces**: Replace SK namespaces with AF namespaces
3. **Update Agent Creation**: Remove Kernel, use direct client creation
4. **Update Method Calls**: Replace `InvokeAsync` with `RunAsync`
5. **Update Thread Creation**: Replace provider-specific constructors with `GetNewThread()`
6. **Update Tool Registration**: Remove attributes, use `AIFunctionFactory.Create()`
7. **Update Options**: Replace `AgentInvokeOptions` with provider-specific options
8. **Test and Validate**: Compile and test all functionality
</configuration_changes>

## Provider-Specific Migration Patterns

<configuration_changes>
The following sections provide detailed migration patterns for each supported provider, covering package references, agent creation patterns, and provider-specific configurations.
</configuration_changes>

### 1. OpenAI Chat Completion Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.OpenAI" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.OpenAI" />
```
</configuration_changes>

**Before (Semantic Kernel):**
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatClient(modelId, apiKey)
    .Build();

ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};

AgentThread thread = new ChatHistoryAgentThread();
```

**After (Agent Framework):**
```csharp
using Microsoft.Agents.AI;
using OpenAI;

AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: "You are a helpful assistant");

AgentThread thread = agent.GetNewThread();
```

### 2. Azure OpenAI Chat Completion Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.OpenAI" />
<PackageReference Include="Azure.AI.OpenAI" />
<PackageReference Include="Azure.Identity" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.OpenAI" />
<PackageReference Include="Azure.AI.OpenAI" />
<PackageReference Include="Azure.Identity" />
```

**Note**: If not using `AzureCliCredential`, you can use `ApiKeyCredential` instead without the `Azure.Identity` package.
</configuration_changes>

**Before (Semantic Kernel):**
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Azure.Identity;

Kernel kernel = Kernel.CreateBuilder()
    .AddAzureOpenAIChatClient(deploymentName, endpoint, new AzureCliCredential())
    .Build();

ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};
```

**After (Agent Framework):**
```csharp
using Microsoft.Agents.AI;
using Azure.AI.OpenAI;
using Azure.Identity;

AIAgent agent = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
    .GetChatClient(deploymentName)
    .CreateAIAgent(instructions: "You are a helpful assistant");
```

### 3. OpenAI Assistants Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.OpenAI" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.OpenAI" />
```
</configuration_changes>

<api_changes>
**Replace this Semantic Kernel pattern:**
```csharp
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;

AssistantClient assistantClient = new(apiKey);
Assistant assistant = await assistantClient.CreateAssistantAsync(
    modelId,
    instructions: "You are a helpful assistant");

OpenAIAssistantAgent agent = new(assistant, assistantClient)
{
    Kernel = kernel
};

AgentThread thread = new OpenAIAssistantAgentThread(assistantClient);
```

**With this Agent Framework pattern:**

**Creating a new assistant:**
```csharp
using Microsoft.Agents.AI;
using OpenAI;

AIAgent agent = new OpenAIClient(apiKey)
    .GetAssistantClient()
    .CreateAIAgent(modelId, instructions: "You are a helpful assistant");

AgentThread thread = agent.GetNewThread();

// Cleanup when needed
await assistantClient.DeleteThreadAsync(thread.ConversationId);
```

**Retrieving an existing assistant:**
```csharp
using Microsoft.Agents.AI;
using OpenAI;

AIAgent agent = new OpenAIClient(apiKey)
    .GetAssistantClient()
    .GetAIAgent(assistantId); // Use existing assistant ID

AgentThread thread = agent.GetNewThread();
```
</api_changes>

### 4. Azure AI Foundry (AzureAIAgent) Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.AzureAI" />
<PackageReference Include="Azure.Identity" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.AzureAI" />
<PackageReference Include="Azure.Identity" />
```
</configuration_changes>

<api_changes>
**Replace these Semantic Kernel patterns:**

**Pattern 1: Direct AzureAIAgent creation**
```csharp
using Microsoft.SemanticKernel.Agents.AzureAI;
using Azure.Identity;

AzureAIAgent agent = new(
    endpoint: new Uri(endpoint),
    credential: new AzureCliCredential(),
    projectId: projectId)
{
    Instructions = "You are a helpful assistant"
};

AgentThread thread = new AzureAIAgentThread(agent);
```

**Pattern 2: PersistentAgent definition creation**
```csharp
// Define the agent
PersistentAgent definition = await client.Administration.CreateAgentAsync(
    deploymentName,
    tools: [new CodeInterpreterToolDefinition()]);

AzureAIAgent agent = new(definition, client);

// Create a thread for the agent conversation.
AgentThread thread = new AzureAIAgentThread(client);
```

**With these Agent Framework patterns:**

**Creating a new agent:**
```csharp
using Microsoft.Agents.AI;
using Azure.AI.Agents.Persistent;
using Azure.Identity;

var client = new PersistentAgentsClient(endpoint, new AzureCliCredential());

// Create a new AIAgent using Agent Framework
AIAgent agent = client.CreateAIAgent(
    model: deploymentName,
    instructions: "You are a helpful assistant",
    tools: [/* List of specialized Azure.AI.Agents.Persistent.ToolDefinition types */]);

AgentThread thread = agent.GetNewThread();
```

**Retrieving an existing agent:**
```csharp
using Microsoft.Agents.AI;
using Azure.AI.Agents.Persistent;
using Azure.Identity;

var client = new PersistentAgentsClient(endpoint, new AzureCliCredential());

// Retrieve an existing AIAgent using its ID
AIAgent agent = await client.GetAIAgentAsync(agentId);

AgentThread thread = agent.GetNewThread();
```
</api_changes>

### 5. A2A Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.A2A" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.A2A" />
```
</configuration_changes>

<api_changes>
**Replace this Semantic Kernel pattern:**
```csharp
// Create an A2A agent instance
using var httpClient = CreateHttpClient();
var client = new A2AClient(url, httpClient);
var cardResolver = new A2ACardResolver(url, httpClient);
var agentCard = await cardResolver.GetAgentCardAsync();
var agent = new A2AAgent(client, agentCard);
```

**With this Agent Framework pattern:**
```csharp
// Initialize an A2ACardResolver to get an A2A agent card.
A2ACardResolver agentCardResolver = new(new Uri(a2aAgentHost));

// Create an instance of the AIAgent for an existing A2A agent specified by the agent card.
AIAgent agent = await agentCardResolver.GetAIAgentAsync();
```
</api_changes>

### 6. OpenAI Responses Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.OpenAI" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.OpenAI" />
```
</configuration_changes>

<api_changes>
**Replace this Semantic Kernel pattern:**

The thread management is done manually with OpenAI Responses in Semantic Kernel, where the thread
needs to be passed to the `InvokeAsync` method and updated with the `item.Thread` from the response.

```csharp
using Microsoft.SemanticKernel.Agents.OpenAI;

// Define the agent
OpenAIResponseAgent agent = new(new OpenAIClient(apiKey))
{
    Name = "ResponseAgent",
    Instructions = "Answer all queries in English and French.",
};

// Initial thread can be null as it will be automatically created
AgentThread? agentThread = null;

var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Input message."), agentThread);
await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
{
    // Update the thread to maintain the conversation for future interaction
    agentThread = responseItem.Thread;

    WriteAgentChatMessage(responseItem.Message);
}
```

**With this Agent Framework pattern:**

Agent Framework automatically manages the thread, so there's no need to manually update it.

```csharp
using Microsoft.Agents.AI.OpenAI;

AIAgent agent = new OpenAIClient(apiKey)
    .GetOpenAIResponseClient(modelId)
    .CreateAIAgent(
        name: "ResponseAgent",
        instructions: "Answer all queries in English and French.",
        tools: [/* AITools */]);

AgentThread thread = agent.GetNewThread();

var result = await agent.RunAsync(userInput, thread);

// The thread will be automatically updated with the new response id from this point
```
</api_changes>

### 7. Azure OpenAI Responses Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.OpenAI" />
<PackageReference Include="Azure.AI.OpenAI" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.OpenAI" />
<PackageReference Include="Azure.AI.OpenAI" />
```
</configuration_changes>

<api_changes>
**Replace this Semantic Kernel pattern:**

Azure OpenAI Responses uses `AzureOpenAIClient` instead of `OpenAIClient`. The thread management is done manually where the thread needs to be passed to the `InvokeAsync` method and updated with the `item.Thread` from the response.

```csharp
using Microsoft.SemanticKernel.Agents.OpenAI;
using Azure.AI.OpenAI;

// Define the agent
OpenAIResponseAgent agent = new(new AzureOpenAIClient(endpoint, new AzureCliCredential()))
{
    Name = "ResponseAgent",
    Instructions = "Answer all queries in English and French.",
};

// Initial thread can be null as it will be automatically created
AgentThread? agentThread = null;

var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Input message."), agentThread);
await foreach (AgentResponseItem<ChatMessageContent> responseItem in responseItems)
{
    // Update the thread to maintain the conversation for future interaction
    agentThread = responseItem.Thread;

    WriteAgentChatMessage(responseItem.Message);
}
```

**With this Agent Framework pattern:**

Agent Framework automatically manages the thread, so there's no need to manually update it.

```csharp
using Microsoft.Agents.AI.OpenAI;
using Azure.AI.OpenAI;

AIAgent agent = new AzureOpenAIClient(endpoint, new AzureCliCredential())
    .GetOpenAIResponseClient(modelId)
    .CreateAIAgent(
        name: "ResponseAgent",
        instructions: "Answer all queries in English and French.",
        tools: [/* AITools */]);

AgentThread thread = agent.GetNewThread();

var result = await agent.RunAsync(userInput, thread);

// The thread will be automatically updated with the new response id from this point
```
</api_changes>

### 8. A2A Migration

<configuration_changes>
**Remove Semantic Kernel Packages:**
```xml
<PackageReference Include="Microsoft.SemanticKernel.Agents.A2A" />
```

**Add Agent Framework Packages:**
```xml
<PackageReference Include="Microsoft.Agents.AI.A2A" />
```
</configuration_changes>

<api_changes>
**Replace this Semantic Kernel pattern:**
```csharp
using A2A;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;

using var httpClient = CreateHttpClient();
var client = new A2AClient(agentUrl, httpClient);
var cardResolver = new A2ACardResolver(url, httpClient);
var agentCard = await cardResolver.GetAgentCardAsync();
Console.WriteLine(JsonSerializer.Serialize(agentCard, s_jsonSerializerOptions));
var agent = new A2AAgent(client, agentCard);
```

**With this Agent Framework pattern:**
```csharp
using System;
using A2A;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.A2A;

// Initialize an A2ACardResolver to get an A2A agent card.
A2ACardResolver agentCardResolver = new(new Uri(a2aAgentHost));

// Create an instance of the AIAgent for an existing A2A agent specified by the agent card.
AIAgent agent = await agentCardResolver.GetAIAgentAsync();
```
</api_changes>

### 9. Unsupported Providers (Require Custom Implementation)

<behavioral_changes>
#### BedrockAgent Migration

**Status**: Hosted Agents is not directly supported in Agent Framework

**Status**: Non-Hosted AI Model Agents supported via `ChatClientAgent`

**Replace this Semantic Kernel pattern:**
```csharp
using Microsoft.SemanticKernel.Agents.Bedrock;

// Create a new agent on the Bedrock Agent service and prepare it for use
using var client =  new AmazonBedrockAgentClient();
using var runtimeClient = new AmazonBedrockAgentRuntimeClient();
var agentModel = await client.CreateAndPrepareAgentAsync(new CreateAgentRequest()
    {
        AgentName = agentName,
        Description = "AgentDescription",
        Instruction = "You are a helpful assistant",
        AgentResourceRoleArn = TestConfiguration.BedrockAgent.AgentResourceRoleArn,
        FoundationModel = TestConfiguration.BedrockAgent.FoundationModel,
    });

// Create a new BedrockAgent instance with the agent model and the client
// so that we can interact with the agent using Semantic Kernel contents.
var agent = new BedrockAgent(agentModel, client, runtimeClient);
```

**With this Agent Framework workaround:**

Currently there's no support for the Hosted Bedrock Agent service in Agent Framework.

For providers like AWS Bedrock that have an `IChatClient` implementation available, use the `ChatClientAgent` directly by providing the `IChatClient` instance to the agent.

_Those agents will be purely backed by the AI chat models behavior and will not store any state in the server._

```csharp
using Microsoft.Agents.AI;

services.TryAddAWSService<IAmazonBedrockRuntime>();
var serviceProvider = services.BuildServiceProvider();
IAmazonBedrockRuntime runtime = serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();

using var bedrockChatClient = runtime.AsIChatClient();
AIAgent agent = new ChatClientAgent(bedrockChatClient, instructions: "You are a helpful assistant");
```
</behavioral_changes>

### Unsupported Features that need workarounds

<behavioral_changes>
The following Semantic Kernel Agents features currently don't have direct equivalents in Agent Framework:

#### Plugins Migration

**Problem**: Semantic Kernel plugins allowed multiple functions to be registered under a type or object instance

**Semantic Kernel pattern**
```csharp
// Create plugin with multiple functions
public class WeatherPlugin
{
    [KernelFunction, Description("Get current weather")]
    public string GetCurrentWeather(string location) 
        => $"Weather in {location}: Sunny";

    [KernelFunction, Description("Get weather forecast")]
    public static Task<string> GetForecastAsync(string location, int days) 
        => Task.FromResult($"Forecast for {location}: {days} days");
}

kernel.Plugins.AddFromType<WeatherPlugin>();
// OR
kernel.Plugins.AddFromObject(new WeatherPlugin());
```

**Agent Framework workaround:**

```csharp
// Create individual functions (no plugin grouping)
public class WeatherFunctions
{
    [Description("Get current weather")]
    public static string GetCurrentWeather(string location) 
        => $"Weather in {location}: Sunny";

    [Description("Get weather forecast")]
    public Task<string> GetForecastAsync(string location, int days) 
        => Task.FromResult($"Forecast for {location}: {days} days");
}

var weatherService = new WeatherFunctions();

// Register functions individually as tools
AITool[] tools = [
    AIFunctionFactory.Create(WeatherFunctions.GetCurrentWeather), // Get from type static method
    AIFunctionFactory.Create(weatherService.GetForecastAsync) // Get from instance method
];

// OR Iterate over the type or instance if many functions are needed for registration
AITool[] tools =
[
    .. typeof(WeatherFunctions)
        .GetMethods(BindingFlags.Static | BindingFlags.Public)
        .Select((m) => AIFunctionFactory.Create(m, target: null)), // Get from type static methods
    .. weatherService.GetType()
        .GetMethods(BindingFlags.Instance | BindingFlags.Public)
        .Select((m) => AIFunctionFactory.Create(m, target: weatherService)) // Get from instance methods
];

AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(
        instructions: "You are a weather assistant",
        tools: tools);
```

#### Prompt Template Migration

**Problem**: Agent prompt templating is not yet supported in Agent Framework

**Semantic Kernel pattern**
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

var template = "Tell a story about {{$topic}} that is {{$length}} sentences long.";

ChatCompletionAgent agent =
    new(templateFactory: new KernelPromptTemplateFactory(),
        templateConfig: new(template) { TemplateFormat = PromptTemplateConfig.SemanticKernelTemplateFormat })
    {
        Kernel = kernel,
        Name = "StoryTeller",
        Arguments = new KernelArguments()
        {
            { "topic", "Dog" },
            { "length", "3" },
        }
    };
```

**Agent Framework workaround**

```csharp
using Microsoft.Agents.AI;
using Microsoft.SemanticKernel; 

// Manually render template
var template = "Tell a story about {{$topic}} that is {{$length}} sentences long.";

var renderedTemplate = await new KernelPromptTemplateFactory()
    .Create(new PromptTemplateConfig(template))
    .RenderAsync(new Kernel(), new KernelArguments()
    {
        ["topic"] = "Dog",
        ["length"] = "3"
    });

AIAgent agent = new OpenAIClient(apiKey)
    .GetChatClient(modelId)
    .CreateAIAgent(instructions: renderedTemplate);

// No template variables in invocation - use plain string
var result = await agent.RunAsync("What's the weather?", thread);
Console.WriteLine(result);
```
</behavioral_changes>

### 10. Function Invocation Filtering

**Invocation Context**

Semantic Kernel's `IAutoFunctionInvocationFilter` provides a `AutoFunctionInvocationContext` where Agent Framework provides `FunctionInvocationContext` 

The property mapping guide from a `AutoFunctionInvocationContext` to a `FunctionInvocationContext` is as follows:

| SK | AF |
| --- | --- |
| RequestSequenceIndex | Iteration |
| FunctionSequenceIndex | FunctionCallIndex |
| ToolCallId | CallContent.CallId |
| ChatMessageContent | Messages[0] |
| ExecutionSettings | Options |
| ChatHistory | Messages |
| Function | Function |
| Kernel | N/A |
| Result | Use `return` from the delegate |
| Terminate | Terminate |
| CancellationToken | provided via argument to middleware delegate |
| Arguments | Arguments |

#### Semantic Kernel

```csharp
// Filter specifically for functions calling
public sealed class CustomAutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
{
    public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
    {
        Console.WriteLine($"[SK Auto Filter] Auto-invoking function: {context.Function.Name}");

        // Check if function should be auto-invoked
        if (context.Function.Name.Contains("Dangerous"))
        {
            Console.WriteLine($"[SK Auto Filter] Skipping dangerous function: {context.Function.Name}");
            context.Terminate = true;
            return;
        }

        await next(context);

        Console.WriteLine($"[SK Auto Filter] Auto-invocation completed for: {context.Function.Name}");
    }
}

var builder = Kernel.CreateBuilder()
    .AddOpenAIChatClient(modelId, apiKey);
    
// via builder DI
var builder = Kernel.CreateBuilder()
    .AddOpenAIChatClient(modelId, apiKey)
    .Services
    .AddSingleton<IAutoFunctionInvocationFilter, CustomAutoFunctionInvocationFilter>();

// OR via DI
services
    .AddKernel()
    .AddOpenAIChatClient(modelId, apiKey)
    .AddSingleton<IAutoFunctionInvocationFilter, CustomAutoFunctionInvocationFilter>();

// OR register auto function filter directly with the kernel instance
kernel.AutoFunctionInvocationFilters.Add(new CustomAutoFunctionInvocationFilter());

// Create agent with filtered kernel
ChatCompletionAgent agent = new()
{
    Instructions = "You are a helpful assistant",
    Kernel = kernel
};
```

#### Agent Framework

Agent Framework provides function calling middleware that offers equivalent capabilities to Semantic Kernel's auto function invocation filters:

```csharp
// Function calling middleware equivalent to CustomAutoFunctionInvocationFilter
async ValueTask<object?> CustomAutoFunctionMiddleware(
    AIAgent agent,
    FunctionInvocationContext context,
    Func<FunctionInvocationContext, CancellationToken, ValueTask<object?>> next,
    CancellationToken cancellationToken)
{
    Console.WriteLine($"[AF Middleware] Auto-invoking function: {context.Function.Name}");

    // Check if function should be auto-invoked
    if (context.Function.Name.Contains("Dangerous"))
    {
        Console.WriteLine($"[AF Middleware] Skipping dangerous function: {context.Function.Name}");
        context.Terminate = true;
        return "Function execution blocked for security reasons";
    }

    var result = await next(context, cancellationToken);

    Console.WriteLine($"[AF Middleware] Auto-invocation completed for: {context.Function.Name}");
    return result;
}

// Apply middleware to agent
var filteredAgent = originalAgent
    .AsBuilder()
    .Use(CustomAutoFunctionMiddleware)
    .Build();
```

### 11. Function Invocation Contexts

**Invocation Context**

Semantic Kernel's `IAutoFunctionInvocationFilter` provides a `AutoFunctionInvocationContext` where Agent Framework provides `FunctionInvocationContext` 

The property mapping guide from a `AutoFunctionInvocationContext` to a `FunctionInvocationContext` is as follows:

| Semantic Kernel | Agent Framework |
| --- | --- |
| RequestSequenceIndex | Iteration |
| FunctionSequenceIndex | FunctionCallIndex |
| ToolCallId | CallContent.CallId |
| ChatMessageContent | Messages[0] |
| ExecutionSettings | Options |
| ChatHistory | Messages |
| Function | Function |
| Kernel | N/A |
| Result | Use `return` from the delegate |
| Terminate | Terminate |
| CancellationToken | provided via argument to middleware delegate |
| Arguments | Arguments |