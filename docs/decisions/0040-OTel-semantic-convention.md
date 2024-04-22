---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
contact: { Tao Chen }
date: { 2024-04-15 }
deciders: {}
consulted: {}
informed: {}
---

# Use standardized vocabulary and specification for observability in Semantic Kernel

## Context and Problem Statement

Observing LLM applications has been a huge ask from customers and the community. This work aims to ensure that SK provides the best developer experience while complying with the industry standards for observability in generative-AI-based applications.

For more information, please refer to this issue: https://github.com/open-telemetry/semantic-conventions/issues/327

### Semantic conventions

The semantic conventions for generative AI are currently in their nascent stage, and as a result, many of the requirements outlined here may undergo changes in the future. Consequently, several features derived from this Architectural Decision Record (ADR) may be considered experimental. It is essential to remain adaptable and responsive to evolving industry standards to ensure the continuous improvement of our system's performance and reliability.

- [Semantic conventions for generative AI](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai)
- [Generic LLM attributes](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/attributes-registry/llm.md)

### Telemetry requirements (Experimental)

Based on the initial version, Semantic Kernel should provide the following attributes in activities that represent LLM requests:

> `Activity` is a .Net concept and existed before OpenTelemetry. A `span` is an OpenTelemetry concept that is equivalent to an `Activity`.

- (Required)`gen_ai.system`
- (Required)`gen_ai.request.model`
- (Recommended)`gen_ai.request.max_token`
- (Recommended)`gen_ai.request.temperature`
- (Recommended)`gen_ai.request.top_p`
- (Recommended)`gen_ai.response.id`
- (Recommended)`gen_ai.response.model`
- (Recommended)`gen_ai.response.finish_reasons`
- (Recommended)`gen_ai.response.prompt_tokens`
- (Recommended)`gen_ai.response.completion_tokens`

The following events will be optionally attached to an activity:
| Event name| Attribute(s)|
|---|---|
|`gen_ai.content.prompt`|`gen_ai.prompt`|
|`gen_ai.content.completion`|`gen_ai.completion`|

> The kernel must provide configuration options to disable these events because they may contain PII.
> See the [Semantic conventions for generative AI](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai) for requirement level for these attributes.

## Where do we create the activities

It is crucial to establish a clear line of responsibilities, particularly since certain service providers, such as the Azure OpenAI SDK, have pre-existing instrumentation (in which case SK won't need to track LLM requests). Our objective is to position our activities as close to the model level as possible to promote a more cohesive and consistent developer experience.

```mermaid
block-beta
columns 1
    Models
    blockArrowId1<["&nbsp;&nbsp;&nbsp;"]>(y)
    block:Clients
        columns 3
        ConnectorTypeClientA["Instrumented client SDK<br>(i.e. Azure OpenAI client)"]
        ConnectorTypeClientB["Un-instrumented Client SDK"]
        ConnectorTypeClientC["Custom client on REST API<br>(i.e. HuggingFaceClient)"]
    end
    Connectors["Connectors/AI Services"]
    blockArrowId2<["&nbsp;&nbsp;&nbsp;"]>(y)
    SemanticKernel["Semantic Kernel"]
    block:Kernel
        Function
        Planner
        Agent
    end
```

> Semantic Kernel also supports other types of connectors for memories/vector databases. We will discuss instrumentations for those connectors in a separate ADR.

> Note that this will not change our approaches to [instrumentation for planners](./0025-planner-telemetry-enhancement.md). We may modify or remove some of the meters we created previously, which will introduce breaking changes.

In order to keep the activities as close to the model level as possible, we should keep them at or below the connector level.

### Out of scope

These services will be discuss in the future:

- Memory/vector database services
- Audio to text services (`IAudioToTextService`)
- Embedding services (`IEmbeddingGenerationService`)
- Image to text services (`IImageToTextService`)
- Text to audio services (`ITextToAudioService`)
- Text to image services (`ITextToImageService`)

## Considered Options

- Instrumentation implementations
  - Static class
  - Dependency injection
- Where do we create the activities
  - Add instrumentations at the connector/service level
  - Add instrumentations at the client level

### Instrumentation implementations

#### Static class `ModelDiagnostics`

This class will live under `SemanticKernel.Abstractions/AI`.

`ModelDiagnostics`

```C#
// Example
public static class ModelDiagnostics
{
    public static Activity? StartCompletionActivity(string name, string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
    {
        ...
    }

    public static Activity? StartCompletionActivity(string name, string modelName, string modelProvider, string prompt, PromptExecutionSettings? executionSettings)
    {
        ...
    }

    // Can be used for both non-streaming endpoints and streaming endpoints.
    // For streaming, collect a list of `StreamingTextContent` and concatenate them into a single `TextContent` at the end of the streaming.
    void SetCompletionResponses(Activity? activity, IReadOnlyList<TextContent> completions, CompletionUsage? usage, PromptExecutionSettings? executionSettings)
    {
        ...
    }

    // Can be used for both non-streaming endpoints and streaming endpoints.
    // For streaming, collect a list of `StreamingChatMessageContent` and concatenate them into a single `ChatMessageContent` at the end of the streaming.
    void SetCompletionResponses(Activity? activity, IReadOnlyList<ChatMessageContent> completions, CompletionUsage? usage, PromptExecutionSettings? executionSettings)
    {
        ...
    }
}
```

Example usage

```C#
// In client
public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
    string prompt,
    PromptExecutionSettings? executionSettings,
    CancellationToken cancellationToken)
{
    using var activity = ModelDiagnostics.StartCompletionActivity(
        $"HuggingFace {this._modelId}",
        this._modelId,
        "HuggingFace",
        prompt,
        executionSettings);

    var completions = ...;
    // Usage can be estimated.
    var usage = ...;

    ModelDiagnostics.SetCompletionResponses(
        activity,
        completions,
        usage,
        executionSettings);

    return completions;
}

// In service
public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
{
    using var activity = ModelDiagnostics.StartCompletionActivity(
        $"HuggingFace {this.AttributesInternal[AIServiceExtensions.ModelIdKey]}",
        this.AttributesInternal[AIServiceExtensions.ModelIdKey],
        "HuggingFace",
        prompt,
        executionSettings);

    var completions = ...;

    // Usage is usually not returned from the clients.
    ModelDiagnostics.SetCompletionResponses(
        activity,
        completions,
        null,
        executionSettings);

    return completions;
}
```

#### Dependency injection

The interface and the implementation will live under `SemanticKernel.Abstractions/AI`.

`DefaultModelInstrumentation : IModelInstrumentation`

```C#
public interface IModelInstrumentation
{
    Activity? StartCompletionActivity(string name, string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings);

    Activity? StartCompletionActivity(string name, string modelName, string modelProvider, string prompt, PromptExecutionSettings? executionSettings);

    void SetCompletionResponses(Activity? activity, IReadOnlyList<TextContent> completions, CompletionUsage? usage);

    void SetCompletionResponses(Activity activity, IReadOnlyList<ChatMessageContent> completions, CompletionUsage? usage);
}

public class DefaultModelInstrumentation : IModelInstrumentation
{
    private readonly bool _isEventCollectionEnabled;

    private readonly ActivitySource s_activitySource = new ActivitySource("model-service");

    public DefaultModelInstrumentation(bool isEventCollectionEnabled)
    {
        _isEventCollectionEnabled = isEventCollectionEnabled;
    }

    ...
}
```

Example usage

```C#
// In client
internal sealed class HuggingFaceClient
{
    ...
    private readonly IModelInstrumentation? _modelInstrumentation;
    ...

    internal HuggingFaceClient(
        string modelId,
        HttpClient httpClient,
        Uri? endpoint = null,
        string? apiKey = null,
        StreamJsonParser? streamJsonParser = null,
        IModelInstrumentation? modelInstrumentation = null,
        ILogger? logger = null)
    {
        ...
        this._modelInstrumentation = modelInstrumentation;
    }

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        using var activity = this._modelInstrumentation.StartCompletionActivity(
            $"HuggingFace {this._modelId}",
            this._modelId,
            "HuggingFace",
            prompt,
            executionSettings);

        var completions = ...;
        // Usage can be estimated.
        var usage = ...;

        this._modelInstrumentation.SetCompletionResponses(
            activity,
            completions,
            usage);

        return completions;
    }
}


// In service
public sealed class HuggingFaceTextGenerationService : ITextGenerationService
{
    public HuggingFaceTextGenerationService(
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        IModelInstrumentation? modelInstrumentation = null)
    {
        ...
        this.Client = new HuggingFaceClient(
            modelId: model,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            modelInstrumentation: modelInstrumentation,
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );
        ...
    }
}
```

Dependency injection example

```C#
builder.Services.AddSingleton<IModelInstrumentation, DefaultModelInstrumentation>();
// In HuggingFaceKernelBuilderExtensions
public static IKernelBuilder AddHuggingFaceTextGeneration(
    this IKernelBuilder builder,
    string model,
    Uri? endpoint = null,
    string? apiKey = null,
    string? serviceId = null,
    HttpClient? httpClient = null)
{
    ...

    builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        new HuggingFaceTextGenerationService(
            model,
            endpoint,
            apiKey,
            HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
            null,
            serviceProvider.GetService<IModelInstrumentation>()
        )
    );

    return builder;
}
```

#### Comparison

Both the static class implementation and the interface approach offer consistent APIs for instrumenting LLM requests. The static class implementation has the advantage of not necessitating modifications to the constructors of services and clients. However, it poses challenges in terms of configuration and future extensibility. On the other hand, the interface approach facilitates convenient configuration and greater expandability, but it necessitates alterations to the constructors.

### Where do we create the activities

#### Connector/AI Service

AI services employ common interfaces and typically feature straightforward implementations, thereby resulting in lower maintenance overhead. Nonetheless, acquiring comprehensive model-related data and complete LLM requests/responses can be challenging within the services.

#### Client

Client implementations may exhibit variations; however, they generally encompass a similar set of methods for text and chat completions. Furthermore, obtaining model data, such as model name and provider, as well as response metadata, including token usage, is more convenient when performed within the clients.

#### Comparison

Clients represent the final layer in the stack through which all kernel operations reach the models. As such, it would be more intuitive to incorporate instrumentation for all LLM requests at the client level. Furthermore, some clients already generate metrics. However, due to the lack of shared interfaces among clients, their instrumentations would need to be implemented individually.

In contrast, connectors (or AI services) share common interfaces, specifically the `IChatCompletionService` and `ITextGenerationService`. Nevertheless, AI services rely on their underlying clients to execute LLM requests, which could potentially result in inconsistencies where telemetry data originates from different layers in the stack if a client is instrumented (e.g., Azure OpenAI vs. `HuggingFaceTextGenerationService`).

|      | Connectors/Services                                                                                           | Clients                                                                                                          |
| ---- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Pros | 1. Uniform implementation across all services.                                                                | 1. Enhanced intuitiveness regarding the overall data flow.<br>2. Complete model specs and LLM requests/response. |
| Cons | 1. Inconsistencies in the origins of telemetry data.<br>2. Incomplete model specs and LLM requests/responses. | 1. Separate implementations may lead to increased maintenance overhead.                                          |

## Decision Outcome

TBD

## Appendix

### `ModelDiagnostics`

```C#
public static class ModelDiagnostics
{
    private static string SourceName = "...";
    private static ActivitySource Source = new ActivitySource(SourceName);

    public static Activity? StartCompletionActivity(string name, string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
    {
        var activity = s_activitySource.StartActivityWithTags(
            name,
            new() {
                new("gen_ai.request.model", modelName),
                new("gen_ai.system", modelProvider),
                ...
            });

        // Chat history is optional as it may contain sensitive data.
        if (executionSettings.IsEventCollectionEnabled)
        {
            activity?.AttachSensitiveDataAsEvent("gen_ai.content.prompt", new() { new("gen_ai.prompt", chatHistory) });
        }

        return activity;
    }
}
```

### `DefaultModelInstrumentation : IModelInstrumentation`

```C#
// Example implementation
public class DefaultModelInstrumentation : IModelInstrumentation
{
    private readonly bool _isEventCollectionEnabled;

    private readonly ActivitySource s_activitySource = new ActivitySource("model-service");

    public DefaultModelInstrumentation(bool isEventCollectionEnabled)
    {
        _isEventCollectionEnabled = isEventCollectionEnabled;
    }

    public Activity? StartCompletionActivity(string name, string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
    {
        var activity = s_activitySource.StartActivityWithTags(
            name,
            new() {
                new("gen_ai.request.model", modelName),
                new("gen_ai.system", modelProvider),
                ...
            });

        if (_isEventCollectionEnabled)
        {
            activity?.AttachSensitiveDataAsEvent("gen_ai.content.prompt", new() { new("gen_ai.prompt", chatHistory) });
        }

        return activity;
    }

    ...
}
```

### Extensions

```C#
public static class ActivityExtensions
{
    public static Activity? StartActivityWithTags(this ActivitySource source, string name, List<KeyValuePair<string, object?>> tags)
    {
        return source.StartActivity(
            name,
            ActivityKind.Internal,
            Activity.current?.Context ?? new ActivityContext(),
            tags);
    }

    public static Activity EnrichAfterResponse(this Activity activity, List<KeyValuePair<string, object?>> tags)
    {
        tags.ForEach(tag => {
            activity.SetTag(tag.Key, tag.Value);
        });

        return activity;
    }

    public static Activity AttachSensitiveDataAsEvent(this Activity activity, string name, List<KeyValuePair<string, object?>> tags)
    {
        activity.AddEvent(new ActivityEvent(
            name,
            tags: new ActivityTagsCollection(tags)
        ));

        return activity;
    }
}
```
