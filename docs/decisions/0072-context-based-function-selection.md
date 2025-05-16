---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: sergeymenshykh
date: 2025-05-13
deciders: markwallace, rbarreto, dmytrostruk, westey-m
consulted: 
informed:
---

## Context and Problem Statement

Currently, Semantic Kernel (SK) advertises **all** functions to the AI model, regardless of their source, whether they are from all registered plugins or provided directly when configuring function choice behavior. This approach works perfectly for most scenarios where there are not too many functions, and the AI model can easily choose the right one.

However, when there are many functions available, AI models may struggle to select the appropriate function, leading to confusion and suboptimal performance. This can result in the AI model calling functions that are not relevant to the current context or conversation, potentially causing the entire scenario to fail.

This ADR consider different options to provide context-based function selection and advertisement mechanism to such components as SK agents, chat completion services, and M.E.AI chat clients.

## Decision Drivers
- It should be possible to advertise functions dynamically based on the context of the conversation.
- It should seamlessly integrate with SK and M.E.AI AI connectors and SK agents.
- It should have access to context and functions without the need for complex plumbing.

## Out of Scope
- A particular implementation of the function selection algorithm whether it's RAG or any other.

## Option 1: External Vectorization and Search

This option is demonstrated in the following sample: [PluginSelectionWithFilters.UsingVectorSearchWithChatCompletionAsync](https://github.com/microsoft/semantic-kernel/blob/6eff772c6034992a9db6e10ac12dd445a19d81a8/dotnet/samples/Concepts/Optimization/PluginSelectionWithFilters.cs#L104C23-L104C63)
which uses the `PluginStore` class to vectorize kernel function and `FunctionProvider` to find functions relevant to the prompt:

````csharp
// Register services
IKernelBuilder builder = Kernel.CreateBuilder();
builder.Services.AddInMemoryVectorStore();
builder.Services.AddSingleton<IFunctionProvider, FunctionProvider>();
builder.Services.AddSingleton<IPluginStore, PluginStore>();

// Register plugins
Kernel kernel = builder.Build();
kernel.ImportPluginFromType<TimePlugin>();
kernel.ImportPluginFromType<WeatherPlugin>();

// Vectorize all functions in the kernel
IPluginStore pluginStore = kernel.GetRequiredService<IPluginStore>();
await pluginStore.SaveAsync(collectionName: "functions", kernel.Plugins);

const string Prompt = "Provide latest headlines";

// Do RAG to find the relevant function for the prompt
IFunctionProvider functionProvider = kernel.GetRequiredService<IFunctionProvider>();
KernelFunction[] relevantFunctions = await functionProvider.GetRelevantFunctionsAsync(collectionName: "functions", Prompt, kernel.Plugins, numberOfFunctions: 1);

// Set the relevant functions to be advertised to the AI model
executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(relevantFunctions);

// Do the chat completion
var chatHistory = new ChatHistory();
chatHistory.AddUserMessage(Prompt);

var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

Console.WriteLine(result);
````

It's invoked per operation rather than per AI model request; one operation call may result in multiple AI model requests in cases where the AI model performs function calling.

Pros:
- Can be used with all AI components, including SK chat completion services, SK agents, and M.E.AI chat clients.

Cons:
- Complex integration of all the parts (vectorization of functions, function search, advertisement of functions) of the solution together.
- Doesn't support function choice behavior configured in prompt templates.

## Option 1A: Function Invocation Filter

This option is demonstrated in the following sample: [PluginSelectionWithFilters.UsingVectorSearchWithKernelAsync](https://github.com/microsoft/semantic-kernel/blob/6eff772c6034992a9db6e10ac12dd445a19d81a8/dotnet/samples/Concepts/Optimization/PluginSelectionWithFilters.cs#L30C23-L30C55).
It's identical to Option 1 for vectorization part and slightly deviates for the function selection part, which is implemented as a function invocation filter that intercepts calls to the `InvokePromptAsync` function,
identifies the relevant functions to the prompt, and sets them to be advertised to the AI model via execution settings:

````csharp
// Register services
IKernelBuilder builder = Kernel.CreateBuilder();
builder.Services.AddInMemoryVectorStore();
builder.Services.AddSingleton<IFunctionProvider, FunctionProvider>();
builder.Services.AddSingleton<IPluginStore, PluginStore>();

// Register plugins
Kernel kernel = builder.Build();
kernel.ImportPluginFromType<TimePlugin>();
kernel.ImportPluginFromType<WeatherPlugin>();

// Vectorize all functions in the kernel
IPluginStore pluginStore = kernel.GetRequiredService<IPluginStore>();
await pluginStore.SaveAsync(collectionName: "functions", kernel.Plugins);

// Register function invocation filter
IFunctionProvider functionProvider = kernel.GetRequiredService<IFunctionProvider>();
kernel.FunctionInvocationFilters.Add(new PluginSelectionFilter(functionProvider: functionProvider, collectionName: "functions"));

// Do the chat completion
KernelArguments kernelArguments = new(executionSettings) { ["Request"] = "Provide latest headlines" };
await kernel.InvokePromptAsync("{{$Request}}", kernelArguments);

// Function invocation filter
class PluginSelectionFilter(IFunctionProvider functionProvider, string collectionName)
{
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        string request = context.Arguments["Request"];

        if (context.Function.Name.Contains(nameof(KernelExtensions.InvokePromptAsync)) && !string.IsNullOrWhiteSpace(request))
        {
            var functions = await functionProvider.GetRelevantFunctionsAsync(collectionName, request, plugins, numberOfFunctions);

            context.Arguments.ExecutionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(functions);
        }

        await next(context);
    }
}
````

It's invoked per operation rather than per AI model request; one operation call may result in multiple AI model requests in cases where the AI model performs function calling. 

Pros:

Cons:
- Relies on usage of the `InvokePromptAsync` function, making it unusable for all scenarios except those where the `kernel.InvokePromptAsync` function is used.
- Doesn't support function choice behavior configured in prompt templates.
 
## Option 2: M.E.AI ChatClient Decorator

This option presumes having an implementation of the `M.E.AI.IChatClient` interface, such as the `ContextFunctionSelectorChatClient` class, which will vectorize all functions available in the
`ChatOptions` parameter of either `GetResponseAsync` or `GetResponseStreamAsync` methods. It will then search for functions relevant to the context represented by the list of chat messages passed to one of these methods:

````csharp
public class ContextFunctionSelectorChatClient : DelegatingChatClient
{
    protected ContextFunctionSelectorChatClient(IChatClient innerClient) : base(innerClient)
    {
    }

    public override async Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null)
    {
        ChatOptions? targetOptions = options;
        if (options?.Tools?.Any() ?? false)
        {
            targetOptions = options.Clone();

            AITool[] functionsToAdvertise = await this.GetRelevantFunctions(options, messages).ConfigureAwait(false);

            targetOptions.Tools = functionsToAdvertise;
        }

        return await base.GetResponseAsync(messages, targetOptions, ct).ConfigureAwait(false);
    }

    private async Task<AITool[]> GetRelevantFunctions(ChatOptions options, IEnumerable<ChatMessage> messages)
    {
        // 1. Vectorize all the functions form the `options.Tool` collection, if not already vectorized.
        // 2. Vectorize the context represented by the `messages` collection.
        // 3. Search for and return the most relevant functions using the vectorized context.
    }

    public override IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null)
    {
        // similar to GetResponseAsync, but for streaming
    }
}

// Usage with M.E.AI chat client
ChatClient chatClient = new("model", "api-key");

IChatClient client = chatClient.AsIChatClient()
    .AsBuilder()
    .UseFunctionInvocation()
    .UseContextFunctionSelector()
    .Build();

// Usage with SK chat completion service
IChatCompletionService chatCompletionService = new OpenAIChatCompletionService("<model-id>", "<api-key>");

IChatClient client = chatCompletionService.AsChatClient()
    .AsBuilder()
    .UseContextFunctionSelector()
    .Build();
````

The decorator is invoked per operation rather than per AI model request; one operation call may result in multiple AI model requests in cases where the AI model performs function calling.

Pros:
- Works seamlessly with SK chat completion services and M.E.AI chat clients.
- Easy wiring aligned with the initialization pattern adopted by M.E.AI.
- No need for a new abstraction.
- Easy to add new function selectors and chain them together.

Cons:
- Works with chat completion agents only and does not work with SK agents that don't use the chat completion service.
- Doesn't support function choice behavior configured in prompt templates.

## Option 3: Function Advertisement Filter

This option assumes having a new filter type that will be used to select the functions to be advertised to the AI model based on the context of the conversation:

````csharp
// Register plugins
Kernel kernel = new Kernel();
kernel.ImportPluginFromType<TimePlugin>();
kernel.ImportPluginFromType<WeatherPlugin>();

// Register function advertisement filter
kernel.FunctionAdvertisementFilters.Add(new ContextFunctionSelectorFilter());

// Do the chat completion
await kernel.InvokePromptAsync("Provide latest headlines");

// Function invocation filter
class ContextFunctionSelectorFilter()
{
    public async Task OnFunctionsAdvertisementAsync(FunctionAdvertisementContext context, Func<FunctionAdvertisementContext, Task> next);
    {
        // 1. Vectorize all the functions form the `context.Functions` collection, if not already vectorized.
        // 2. Vectorize the context represented by the `context.ChatHistory` collection.
        // 3. Search for and assign the most relevant functions using the vectorized context to `context.Functions` property.
    }
}
````

The filter can be invoked per operation and per AI model request as well; one operation call may result in multiple AI model requests in cases where the AI model performs function calling.

Pros:
- Familiar concept for SK users.
- Works with chat completion services.
- Works with both chat completion and non-chat completion **SK** agents, provided they can provide context to the filter.

Cons:
- New abstraction is required.
- Public API surface of Kernel needs to be extended.
- All AI components: SK agents, chat completion services, and M.E.AI chat clients adapters need to be updated to invoke the filter.

## Option 4: FunctionChoiceBehavior Callback

This options presume extending the existing `AutoFunctionChoiceBehavior`, `RequiredFunctionChoiceBehavior` and `NoneFunctionChoiceBehavior` classes with a new constructor that 
takes a function selector as a parameter and uses it to select the functions based on the context to be advertised to the AI model.

````csharp
// Register services
IKernelBuilder builder = Kernel.CreateBuilder();
builder.Services.AddInMemoryVectorStore();
builder.Services.AddSingleton<IFunctionProvider, FunctionProvider>();
builder.Services.AddSingleton<IPluginStore, PluginStore>();

// Register plugins
Kernel kernel = builder.Build();
kernel.ImportPluginFromType<TimePlugin>();
kernel.ImportPluginFromType<WeatherPlugin>();

// Set the relevant functions to be advertised to the AI model
executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(FunctionSelector);

// Do the chat completion
var chatHistory = new ChatHistory();
chatHistory.AddUserMessage("Provide latest headlines");

var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

Console.WriteLine(result);

async Task<IList<KernelFunction>> FunctionSelector(FunctionChoiceBehaviorConfigurationContext context)
{
    // Vectorize all the functions form the `context.Functions` collection
    IPluginStore pluginStore = context.Kernel.GetRequiredService<IPluginStore>();
    await pluginStore.SaveAsync(collectionName: "functions", context.Kernel.Plugins);

    // Search for the most relevant functions using the vectorized context
    IFunctionProvider functionProvider = kernel.GetRequiredService<IFunctionProvider>();
    IList<KernelFunction> relevantFunctions = await functionProvider.GetRelevantFunctionsAsync(collectionName: "functions", context.ChatHistory, kernel.Plugins, numberOfFunctions: 1);

    return relevantFunctions;
}
````

The filter can be invoked per operation and per AI model request as well; one operation call may result in multiple AI model requests in cases where the AI model performs function calling.

Pros:

Cons:
- Doesn't support function choice behavior configured in prompt templates.
- Can only be used by components that use `FunctionChoiceBehavior`: SK chat completion services and chat completion agents.

## Options Applicability

This table summarizes the applicability of the options described above to the different components of the Semantic Kernel and M.E.AI:

| Option                                 | Scope     | OpenAI & AzureAI Agents | Bedrock Agent         | Chat Completion Agent | SK Chat Completion Service | M.E.AI Chat Client   |
|----------------------------------------|-----------|-------------------------|-----------------------|-----------------------|----------------------------|----------------------|
| **1.** External Vectorization & Search | Operation | Yes<sup>1,2</sup>       | Yes<sup>1,3</sup>     | Yes<sup>1,2or4</sup>  | Yes<sup>1,2or4</sup>       | Yes<sup>1</sup>      |
| **1A.** Function Invocation Filter     | Operation | No<sup>5</sup>          | No<sup>5</sup>        | No<sup>5</sup>        | No<sup>5</sup>             | No                   |
| **2.** M.E.AI ChatClient Decorator     | Operation | No                      | No                    | Yes<sup>6</sup>       | Yes<sup>6</sup>            | Yes                  |
| **3.** Function Advertisement Filter   | Op & Req  | Yes                     | No<sup>3</sup>        | Yes                   | Yes                        | Yes<sup>7</sup>      |
| **4.** FunctionChoiceBehavior Callback | Op & Req  | No<sup>8,9</sup>        | No<sup>8</sup>        | Yes                   | Yes                        | Yes<sup>7</sup>      |

<sup>1</sup> Requires manual orchestration of function vectorization, function search, function advertisement, and agent/chat completion service invocation.
This solution is available today but requires complex plumbing to integrate all the components together.

<sup>2</sup> To supply relevant functions for each invocation of the agent or chat completion service, all plugins registered in the kernel need to be removed first. 
Then, a new plugin with relevant functions needs to be registered on the kernel using `kernel.Plugins.AddFromFunctions("dynamicPlugin", [relevantFunctions])` for each invocation.
Alternatively, instead of removing the plugins, a new kernel can be created; however, a new instance of the agent needs to be created as well.
The fact that the relevant functions will no longer be part of their original plugins and will be repackaged into a new plugin may introduce some problems, such as function name collisions 
and loss of the additional context provided by the original plugin.

<sup>3</sup> To supply relevant functions for each agent invocation, a new instance of agent needs to be created per invocation because the agent uses functions defined 
in the `AgentDefinition.Tools` collection, which is used only at the time of agent initialization.

<sup>4</sup> To supply relevant functions for each invocation of the agent or chat completion service, the orchestration functionality needs to provide them via the `functions` parameter of a new instance of one 
of the `*FunctionChoiceBehavior` class and assign that instance to the `executionSettings.FunctionChoiceBehavior` property: `executionSettings.FunctionChoiceBehavior = new AutoFunctionChoiceBehavior(functions)`.

<sup>5</sup> Uses a function invocation filter to perform function selection and advertisement. The filter searches for the relevant functions and sets them to be advertised to the AI 
model via execution settings only if triggered by the invocation of the `kernel.InvokePromptAsync` function. It does nothing if triggered by other function invocations, making this option unusable in 
all cases except those where the `kernel.InvokePromptAsync` function is used.

<sup>6</sup> M.E.AI Chat Client needs to be adapted to the `IChatCompletionService` interface using the `ChatClientChatCompletionService` SK adapter.

<sup>7</sup> M.E.AI Chat Client needs to be decorated (the decorator is available in SK) so the decorator can access the function advertisement filter/function choice behavior to get the relevant functions.

<sup>8</sup> Neither OpenAI, AzureAI, nor Bedrock agents use function choice behavior for function advertisement. Extending any of the agents to use function choice behavior 
does not make any sense because they do not support any other function choice behavior except auto function choice behavior.

<sup>9</sup> Extending either OpenAI or AzureAI agents to obtain relevant functions from the provided function choice behavior will make the development experience confusing.
Currently, functions can be sourced to agents from three places: agent definition, agent constructor, and kernel. Adding a fourth source will make it even more confusing.

Notes:
- For agents that maintain threads on the server side, getting the full context is impossible without first loading the entire thread from the server.
This is not efficient and might not be supported by agents. However, the messages passed during agent invocation might be enough and can be used as context for function selection.

## Integration with Agent Memory

The agent's memory model is represented by the following classes:

````csharp
public sealed class AIContextPart
{
    public string? Instructions { get; set; }
    public List<AIFunction> AIFunctions { get; set; } = new();
}

public abstract class AIContextBehavior
{
    public virtual Task OnThreadCreatedAsync(string? threadId, CancellationToken ct) {...}
    public virtual Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken ct) {...}
    public virtual Task OnThreadDeleteAsync(string? threadId, CancellationToken ct) {...}
    public abstract Task<AIContextPart> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken ct);
    public virtual Task OnSuspendAsync(string? threadId, CancellationToken ct) {...}
    public virtual Task OnResumeAsync(string? threadId, CancellationToken ct) {...}
}

public sealed class AIContextBehaviorsManager
{
    public AIContextBehaviorsManager(IEnumerable<AIContextBehavior> aiContextBehaviors) {...}
    public void Add(AIContextBehavior aiContextBehavior) {...}
    public void AddFromServiceProvider(IServiceProvider serviceProvider) {...}
    public async Task OnThreadCreatedAsync(string? threadId, CancellationToken ct) {...}
    public async Task OnThreadDeleteAsync(string threadId, CancellationToken ct) {...}
    public async Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken ct) {...}
    public async Task<AIContextPart> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken ct) {...}
    public async Task OnSuspendAsync(string? threadId, CancellationToken ct) {...}
    public async Task OnResumeAsync(string? threadId, CancellationToken ct) {...}
}
````

An example demonstrating the model's usage:

````csharp
// Create a kernel and register plugins
Kernel kernel = this.CreateKernelWithChatCompletion();
kernel.Plugins.AddFromType<FinancePlugin>();

// Create Mem0Behavior
Mem0Behavior mem0Behavior = new(...);
await mem0Behavior.ClearStoredMemoriesAsync();

// Create a chat completion agent
ChatCompletionAgent agent = new(kernel, ...);

// Create agent thread and add Mem0Behavior to it
ChatHistoryAgentThread agentThread = new();    
agentThread.AIContextBehaviors.Add(mem0Behavior);

// Prompt the agent
string userMessage = "Please retrieve my company report";
ChatMessageContent message = await agent.InvokeAsync(userMessage, agentThread).FirstAsync();
````

There might be cases when there is a need to reuse an existing AI context behavior to narrow down the list of functions for non-agent scenarios, such as a chat completion service or chat client.
In these cases, either the AI context behavior can be adapted to the model required by one of the options described above, or preferably the same components for vectorization and 
semantic search can be used to implement both the AI context behavior and the model required by one of the options described above.

## Decision Outcome
During the ADR review meeting, it was decided to prioritize context-based function selection for agents by implementing an AIContextBehavior, which would perform RAG on the agent's functions.
Later, upon request, the same functionality can be extended to chat completion services and  M.E.AI chat clients using option 2: the M.E.AI ChatClient Decorator.