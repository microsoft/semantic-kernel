---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
contact: { Tao Chen }
date: { 2024-04-15 }
deciders: {}
consulted: { Ben Thomas, Liudmila Molkova, Stephen Toub }
informed: { Dmytro Struk, Mark Wallace }
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

Based on the initial version, Semantic Kernel should provide the following attributes in activities that represent individual LLM requests:

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

It is crucial to establish a clear line of responsibilities, particularly since certain service providers, such as the Azure OpenAI SDK, have pre-existing instrumentation. Our objective is to position our activities as close to the model level as possible to promote a more cohesive and consistent developer experience.

```mermaid
block-beta
columns 1
    Models
    blockArrowId1<["&nbsp;&nbsp;&nbsp;"]>(y)
    block:Connectors
        columns 3
        ConnectorTypeClientA["Instrumented client SDK<br>(i.e. Azure OpenAI client)"]
        ConnectorTypeClientB["Un-instrumented Client SDK"]
        ConnectorTypeClientC["Custom client on REST API<br>(i.e. HuggingFaceClient)"]
    end
    Services["AI Services"]
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

In order to keep the activities as close to the model level as possible, we should keep them at the connector level.

### Out of scope

These services will be discuss in the future:

- Memory/vector database services
- Audio to text services (`IAudioToTextService`)
- Embedding services (`IEmbeddingGenerationService`)
- Image to text services (`IImageToTextService`)
- Text to audio services (`ITextToAudioService`)
- Text to image services (`ITextToImageService`)

## Considered Options

- Scope of Activities
  - All connectors, irrespective of the client SDKs used.
  - Connectors that either lack instrumentation in their client SDKs or use custom clients.
  - All connectors, noting that the attributes of activities derived from connectors and those from instrumented client SDKs do not overlap.
- Implementations of Instrumentation
  - Static class
- Switches for experimental features and the collection of sensitive data
  - App context switch

### Scope of Activities

#### All connectors, irrespective of the client SDKs utilized

All AI connectors will generate activities for the purpose of tracing individual requests to models. Each activity will maintain a **consistent set of attributes**. This uniformity guarantees that users can monitor their LLM requests consistently, irrespective of the connectors used within their applications. However, it introduces the potential drawback of data duplication which **leads to greater costs**, as the attributes contained within these activities will encompass a broader set (i.e. additional SK-specific attributes) than those generated by the client SDKs, assuming that the client SDKs are likewise instrumented in alignment with the semantic conventions.

#### Connectors that either lack instrumentation in their client SDKs or utilize custom clients

AI connectors paired with client SDKs that lack the capability to generate activities for LLM requests will take on the responsibility of creating such activities. In contrast, connectors associated with client SDKs that do already generate request activities will not be subject to further instrumentation. It is required that users subscribe to the activity sources offered by the client SDKs to ensure consistent tracking of LLM requests. This approach helps in **mitigating the costs** associated with unnecessary data duplication. However, it may introduce **inconsistencies in tracing**, as not all LLM requests will be accompanied by connector-generated activities.

#### All connectors, noting that the attributes of activities derived from connectors and those from instrumented client SDKs do not overlap

All connectors will generate activities for the purpose of tracing individual requests to models. The composition of these connector activities, specifically the attributes included, will be determined based on the instrumentation status of the associated client SDK. The aim is to include only the necessary attributes to prevent data duplication. Initially, a connector linked to a client SDK that lacks instrumentation will generate activities encompassing all potential attributes as outlined by the LLM semantic conventions, alongside some SK-specific attributes. However, once the client SDK becomes instrumented in alignment with these conventions, the connector will cease to include those previously added attributes in its activities, avoiding redundancy. This approach facilitates a **relatively consistent** development experience for user building with SK while **optimizing costs** associated with observability.

### Instrumentation implementations

#### Static class `ModelDiagnostics`

This class will live under `dotnet\src\InternalUtilities\src\Diagnostics`.

```C#
// Example
namespace Microsoft.SemanticKernel;

internal static class ModelDiagnostics
{
    // Consistent namespace for all connectors
    private static string s_namespace = typeof(ModelDiagnostics).Namespace;
    private static ActivitySource s_activitySource = new ActivitySource(s_namespace);

    public static Activity? StartCompletionActivity(string name, string modelName, string modelProvider, string prompt, PromptExecutionSettings? executionSettings)
    {
        ...
    }

    public static Activity? StartCompletionActivity(string name, string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
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

    // Will contain more features in the future for embedding generation
    ...
}
```

Example usage

```C#
public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
    string prompt,
    PromptExecutionSettings? executionSettings,
    CancellationToken cancellationToken)
{
    using var activity = ModelDiagnostics.StartCompletionActivity(
        $"text.generation {this._modelId}",
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
```

## Decision Outcome

TBD

## Appendix

### `PromptExecutionSettings`

```C#
public class PromptExecutionSettings
{
    ...
    [JsonPropertyName("is_event_collection_enable")]
    public bool IsEventCollectionEnabled
    {
        get => this._isEventCollectionEnabled;

        set
        {
            this.ThrowIfFrozen();
            this._isEventCollectionEnabled = value;
        }
    }
    ...
    private bool _isEventCollectionEnabled = false;
}
```

### `ModelDiagnostics` (static class)

```C#
private static class ModelDiagnostics
{
    ...
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
    ...
}
```

### `ModelDiagnostics` (static member)

```C#
internal sealed class ModelDiagnostics
{
    private readonly ActivitySource _source;

    // Source name must be unique
    public ModelDiagnostics(string sourceName)
    {
        this._source = new ActivitySource(sourceName);
    }

    public Activity? StartCompletionActivity(string name, string modelName, string modelProvider, string prompt, PromptExecutionSettings? executionSettings)
    {
        var activity = this._source.StartActivityWithTags(
            name,
            new() {
                new("gen_ai.request.model", modelName),
                new("gen_ai.system", modelProvider),
                ...
            });

        // Chat history is optional as it may contain sensitive data.
        if (executionSettings.IsEventCollectionEnabled)
        {
            activity?.AttachSensitiveDataAsEvent("gen_ai.content.prompt", new() { new("gen_ai.prompt", prompt) });
        }

        return activity;
    }

    ...
}
```

### `ModelDiagnostics` (dependency injection)

```C#
// Example implementation
internal class ModelDiagnostics
{
    ...

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
