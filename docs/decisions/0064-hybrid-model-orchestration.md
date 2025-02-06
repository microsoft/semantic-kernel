---
status: proposed
contact: sergeymenshykh
date: 2025-02-05
deciders: dmytrostruk, markwallace, rbarreto, sergeymenshykh, westey-m,
---

# Hybrid Model Orchestration

## Context and Problem Statement
Taking into account the constantly emerging and improving local and cloud-based models, in addition to the growing demand for utilizing local AI models running on local devices' NPUs, 
AI powered applications need to be able to effectively and seamlessly leverage both local and cloud models for inference to achieve the best AI user experience.

## Decision Drivers

1. The model orchestration layer should be simple and extensible.
2. The model orchestration layer client code should not be aware of or deal with the underlying complexities.
3. The model orchestration layer should allow for different strategies for selecting the best model(s) for the task at hand.
4. The model orchestration layer can be configured declaratively.

## Considered Implementation Options

The following options consider a few ways to implement the model orchestration layer.

### Option 1: IChatClient implementation per orchestration strategy

This option presents a simple and straightforward approach to implementing the model orchestration layer. Each strategy is implemented as a separate implementation of the IChatClient interface. 

For example, a fallback strategy that uses the first configured chat client for inference and falls back to the next one if the AI model is not available may be implemented as follows:
```csharp
public sealed class FallbackChatClient : IChatClient
{
    private readonly IChatClient[] _clients;

    public FallbackChatClient(params IChatClient[] clients)
    {
        this._clients = clients;
    }

    public Task<Microsoft.Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        foreach (var client in this._clients)
        {
            try
            {
                return client.CompleteAsync(chatMessages, options, cancellationToken);
            }
            catch (HttpRequestException ex)
            {
                if (ex.StatusCode >= 500)
                {
                    // Try the next client
                    continue;
                }

                throw;
            }
        }
    }

    public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        ...
    }

    public void Dispose() { /*We can't dispose clients here because they can be used up the stack*/ }

    public ChatClientMetadata Metadata => new ChatClientMetadata();

    public object? GetService(Type serviceType, object? serviceKey = null) => null;
}
```

Other orchestration strategies, such as latency-based or token-based strategies, can be implemented in a similar way: a class that implements the IChatClient interface and the corresponding chat client selection strategy.

Pros:
- Simple and straightforward implementation.
- Can be sufficient for most use cases.

Cons:
- Can't be reused to create more complex scenarios.


### Option 2: HybridChatClient class with chat copletion handler(s) per orchestration strategy

This option introduces a HybridChatClient class that implements the IChatClient interface and delegates the selection routine to a provided handler represented by the abstract ChatCompletionHandler class:
```csharp
public sealed class HybridChatClient : IChatClient
{
    private readonly IChatClient[] _chatClients;
    private readonly ChatCompletionHandler _handler;
    private readonly Kernel? _kernel;

    public HybridChatClient(IChatClient[] chatClients, ChatCompletionHandler handler, Kernel? kernel = null)
    {
        this._chatClients = chatClients;
        this._handler = handler;
        this._kernel = kernel;
    }

    public Task<Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this._handler.CompleteAsync(
            new ChatCompletionHandlerContext
            {
                ChatMessages = chatMessages,
                Options = options,
                ChatClients = this._chatClients.ToDictionary(c => c, c => (CompletionContext?)null),
                Kernel = this._kernel,
            }, cancellationToken);
    }

    public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        ...
    }

    ...
}

public abstract class ChatCompletionHandler : IDisposable
{
    public abstract Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public abstract IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public virtual void Dispose()
    {
    }
}
```

The HybridChatClient class passes all the necessary information to the handler via the ChatCompletionHandlerContext class, which contains the list of chat clients, chat messages, options, and Kernel instance.
```csharp
public class ChatCompletionHandlerContext
{
    public IDictionary<IChatClient, CompletionContext?> ChatClients { get; init; }

    public IList<ChatMessage> ChatMessages { get; init; }

    public ChatOptions? Options { get; init; }

    public Kernel? Kernel { get; init; }
}
```

The fallback strategy shown in the previous option can be implemented as the following handler:
```csharp
public class FallbackChatCompletionHandler : ChatCompletionHandler
{
    public override async Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        for (int i = 0; i < context.ChatClients.Count; i++)
        {
            var chatClient = context.ChatClients.ElementAt(i).Key;

            try
            {
                return client.CompleteAsync(chatMessages, options, cancellationToken);
            }
            catch (HttpRequestException ex)
            {
                if (ex.StatusCode >= 500)
                {
                    // Try the next client
                    continue;
                }

                throw;
            }
        }

        throw new InvalidOperationException("No client provided for chat completion.");
    }

    public override async IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        ...
    }
}
```

and the caller code would look like this:
```csharp
IChatClient onnxChatClient = new OnnxChatClient(...);

IChatClient openAIChatClient = new OpenAIChatClient(...);

// Tries the first client and falls back to the next one if the first one fails
FallbackChatCompletionHandler handler = new FallbackChatCompletionHandler(...);

IChatClient hybridChatClient = new HybridChatClient([onnxChatClient, openAIChatClient], handler);

...

var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", ...);
```

The handlers can be chained to create more complex scenarios, where a handler performs some preprocessing and then delegates the call to another handler with an augmented chat clients list. 

For example, the first handler identifies that a cloud model has requested access to sensitive data and delegates the call handling to local models to process it.

```csharp
IChatClient onnxChatClient = new OnnxChatClient(...);

IChatClient llamaChatClient = new LlamaChatClient(...);

IChatClient openAIChatClient = new OpenAIChatClient(...);

// Tries the first client and falls back to the next one if the first one fails
FallbackChatCompletionHandler fallbackHandler = new FallbackChatCompletionHandler(...);
  
// Check if the request contains sensitive data, identifies the client(s) allowed to work with the sensitive data, and delegates the call handling to the next handler.
SensitiveDataHandler sensitiveDataHandler = new SensitiveDataHandler(fallbackHandler);

IChatClient hybridChatClient = new HybridChatClient(new[] { onnxChatClient, llamaChatClient, openAIChatClient }, sensitiveDataHandler);
  
var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", ...);
```

Examples of complex orchestration scenarios:

| First Handler                         | Second Handler                 | Scenario Description                                                      |    
|---------------------------------------|--------------------------------|---------------------------------------------------------------------------|    
| InputTokenThresholdEvaluationHandler  | FastestChatCompletionHandler   | Identifies models based on the prompt's input token size and each model's min/max token capacity, then returns the fastest model's response. |
| InputTokenThresholdEvaluationHandler  | RelevancyChatCompletionHandler | Identifies models based on the prompt's input token size and each model's min/max token capacity, then returns the most relevant response. |
| InputTokenThresholdEvaluationHandler  | FallbackChatCompletionHandler  | Identifies models based on the prompt's input token size and each model's min/max token capacity, then returns the first available model's response. |
| SensitiveDataRoutingHandler           | FastestChatCompletionHandler   | Identifies models based on data sensitivity, then returns the fastest model's response. |
| SensitiveDataRoutingHandler           | RelevancyChatCompletionHandler | Identifies models based on data sensitivity, then returns the most relevant response. |
| SensitiveDataRoutingHandler           | FallbackChatCompletionHandler  | Identifies models based on data sensitivity, then returns the first available model's response. |

Pros:
- Allows reusing same handlers to create various composite orchestration strategies.

Cons:
- Requires slightly more components than the previous option: context classes and code for handling the next handler.

<br/>

POC demonstrating this option can be found [here](https://github.com/microsoft/semantic-kernel/pull/10412).
 
## Considered Declaration Options

This section contains only one considered option for the declarative configuration of the model orchestration layer. 
The other options will be considered in the scope of the [.Net: Az Template Support](https://github.com/microsoft/semantic-kernel/issues/10149), where chat clients and agents need to be configured declaratively.

### Option 1: Factory-based configuration with DI

This deployment option presumes having a factory per component to create and configure the components and DI for wiring them together.

The JSON declaration for chat clients may look like this:

```json
{
    "services": [ 
        {
            "serviceKey": "openAIClient",
            "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
            "lifetime": "Singleton",
            "factory": {
                "type": "ChatCompletion.Hybrid.OpenAIChatClientFactory, Concepts",
                "configuration": {
                    "useFunctionInvocation": true,
                    "chatModel": "gpt4o",
                    "credential": {
                        "type": "System.ClientModel.ApiKeyCredential, System.ClientModel",
                        "apiKeySecretName": "openAIApiSecret"
                    }
                }
            }
        },
        {
            "serviceKey": "azureOpenAIClient",
            "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
            "lifetime": "Singleton",
            "factory": {
                "type": "ChatCompletion.Hybrid.AzureOpenAIChatClientFactory, Concepts",
                "configuration": {
                    "useFunctionInvocation": true,
                    "chatModel": "gpt4o-mini",
                    "deploymentSecretName": "azure",
                    "credential": 
                    {
                        "type": "Azure.Identity.AzureCliCredential, Azure.Identity"
                    }
                }
            }
        },
        {
            "serviceKey": "hybridChatClient",
            "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
            "lifetime": "Singleton",
            "factory": {
                "type": "ChatCompletion.Hybrid.HybridChatClientFactory, Concepts",
                "configuration": {
                    "clients": ["openAIClient", "azureOpenAIClient"]
                }
            }
        }
    ]  
}  
```

The factory classes would look like this:
```csharp
internal sealed class OpenAIChatClientFactory
{
    private readonly OpenAIChatClientConfiguration _config;

    public OpenAIChatClientFactory(IServiceProvider serviceProvider, JsonElement config)
    {
        this._config = config.Deserialize<OpenAIChatClientConfiguration>()!;
    }

    public Microsoft.Extensions.AI.IChatClient Create()
    {
        IChatClient openAiClient = new OpenAIClient(_config.Credential).AsChatClient(_config.ChatModel);

        var builder = new ChatClientBuilder(openAiClient);

        if (this._config.UseFunctionInvocation)
        {
            builder.UseFunctionInvocation();
        }

        return builder.Build();
    }
}

internal sealed class HybridChatClientFactory
{
    private readonly HybridChatClientConfiguration _configuration;
    private readonly IServiceProvider _serviceProvider;

    public HybridChatClientFactory(IServiceProvider serviceProvider, JsonElement configuration)
    {
        this._serviceProvider = serviceProvider;
        this._configuration = configuration.Deserialize<HybridChatClientConfiguration>()!;
    }

    public Microsoft.Extensions.AI.IChatClient Create()
    {
        FallbackChatCompletionHandler handler = new();

        var chatClients = this._configuration.Clients.Select(this._serviceProvider.GetRequiredKeyedService<IChatClient>);

        var kernel = this._serviceProvider.GetService<Kernel>();

        return new HybridChatClient(chatClients, handler, kernel);
    }
}
```

The application bootstrap code might like this:
```csharp
using var configuration = new MemoryStream(System.Text.Encoding.UTF8.GetBytes("""
{
    "services": [ 
        {
            "serviceKey": "openAIClient",
            ...
        },
        {
            "serviceKey": "azureOpenAIClient",
            ..
        },
        {
            "serviceKey": "hybridChatClient",
            ...
        }
    ]  
}  
"""));

var services = new ServiceCollection();

ServiceRegistry.RegisterServices(services, configuration);

var serviceProvider = services.BuildServiceProvider();

var hybridChatClient = serviceProvider.GetRequiredKeyedService<IChatClient>("hybridChatClient");

var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", ...);
```

This option was prototyped [here](https://github.com/SergeyMenshykh/semantic-kernel/blob/27676638600120d0d87ac151cc7dea9a6b7d9c92/dotnet/samples/Concepts/ChatCompletion/Hybrid/SwitchingBetweenLocalAndCloudModels.cs#L72).

Pros:
- No need to change declarative configuration rendering code to support new components.

Cons:
- Requires a factory per component.
 
## Decision Outcome

TBD