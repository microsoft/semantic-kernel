---
status: accepted
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
- Does not require any new abstraction.
- Simple and straightforward implementation.
- Can be sufficient for most use cases.

### Option 2: HybridChatClient class with chat completion handler(s) per orchestration strategy

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

public abstract class ChatCompletionHandler
{
    public abstract Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);

    public abstract IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default);
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
- Requires new abstractions and components than the previous option: context classes and code for handling the next handler.

<br/>

POC demonstrating this option can be found [here](https://github.com/microsoft/semantic-kernel/pull/10412).

### Option 3: Implementing existing IAIServiceSelector interface.

The Semantic Kernel has a mechanism that allows for the dynamic selection of AI services:

```csharp
public interface IAIServiceSelector
{
    bool TrySelectAIService<T>(
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments,
        [NotNullWhen(true)] out T? service,
        out PromptExecutionSettings? serviceSettings) where T : class, IAIService;
}
```

However, this mechanism requires specific context - the kernel, function, and arguments which may not always be available.
Additionally, it only works with implementations of the IAIService interface, which may not be compatible with all AI services, 
such as those in Microsoft.Extensions.AI that implement the IChatClient interface.

Furthermore, this mechanism cannot be used in orchestration scenarios where an AI service needs to be prompted first to determine its availability, latency, etc.
For example, to check if an AI service is available, the selector would need to send chat messages with options to the service. It should then return 
the completion if the service is available, or fallback to another service if it is not. Given that the TrySelectAIService method does not accept a list of 
chat messages or options, it is impossible to send chat messages using this method. Even if it were possible, the consumer code would have to resend the same 
chat messages to the selected service to obtain a completion, as the selector does not return the completion itself. Additionally, the TrySelectAIService method 
is synchronous, making it difficult to send chat messages without using synchronous code, which is generally discouraged.

Looking at the above, it is clear that the IAIServiceSelector interface is not suitable for the hybrid orchestration of AI services since it was designed for a different purpose: 
to synchronously select an instance of an AI service based on SK context and service metadata without taking the results of completion and streamed completion methods into account.

Pros:
- Reuses the existing mechanism for AI service selection.

Cons:
- Not suitable for all AI services.
- Requires context that may not be available in all scenarios.
- Consumer code must be aware of the IAIServiceSelector interface instead of simply using the IChatClient interface.
- Synchronous method.

## Decision Outcome

Chosen option: Option 1 because it does not require any new abstraction; its simplicity and straightforwardness are sufficient for most use cases. 
Option 2 can be considered in the future if more complex orchestration scenarios are required.