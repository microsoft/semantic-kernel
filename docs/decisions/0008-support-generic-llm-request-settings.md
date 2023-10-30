---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: markwallace-microsoft
date: 2023-=9-15
deciders: shawncal
consulted: stoub, lemiller, dmytrostruk
informed: 
---
# Refactor to support generic LLM request settings

## Context and Problem Statement

The Semantic Kernel abstractions package includes a number of classes ([CompleteRequestSettings](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextCompletion/CompleteRequestSettings.cs), [ChatRequestSettings](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/ChatRequestSettings.cs) [PromptTemplateConfig.CompletionConfig](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/SemanticFunctions/PromptTemplateConfig.cs#L18C1-L82C6)) which are used to support:

1. Passing LLM request settings when invoking an AI service
2. Deserialization of LLM requesting settings when loading the `config.json` associated with a Semantic Function

The problem with these classes is they include OpenAI specific properties only. A developer can only pass OpenAI specific requesting settings which means:

1. Settings may be passed that have no effect e.g., passing `MaxTokens` to Huggingface
2. Settings that do not overlap with the OpenAI properties cannot be sent e.g., Oobabooga supports additional parameters e.g., `do_sample`, `typical_p`, ...

Link to issue raised by the implementer of the Oobabooga AI service: <https://github.com/microsoft/semantic-kernel/issues/2735>

## Decision Drivers

* Semantic Kernel abstractions must be AI Service agnostic i.e., remove OpenAI specific properties.
* Solution must continue to support loading Semantic Function configuration (which includes AI request settings) from `config.json`.
* Provide good experience for developers e.g., must be able to program with type safety, intellisense, etc.
* Provide a good experience for implementors of AI services i.e., should be clear how to define the appropriate AI Request Settings abstraction for the service they are supporting.
* Semantic Kernel implementation and sample code should avoid specifying OpenAI specific request settings in code that is intended to be used with multiple AI services.
* Semantic Kernel implementation and sample code must be clear if an implementation is intended to be OpenAI specific.

## Considered Options

* Use `dynamic` to pass request settings
* Use `object` to pass request settings
* Define a base class for AI request settings which all implementations must extend

Note: Using generics was discounted during an earlier investigation which Dmytro conducted.

## Decision Outcome

**Proposed:** Define a base class for AI request settings which all implementations must extend.

## Pros and Cons of the Options

### Use `dynamic` to pass request settings

The `IChatCompletion` interface would look like this:

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

Developers would have the following options to specify the requesting settings for a semantic function:

```csharp
// Option 1: Use an anonymous type
await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?", requestSettings: new { MaxTokens = 256, Temperature = 0.7 });

// Option 2: Use an OpenAI specific class
await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAIRequestSettings() { MaxTokens = 256, Temperature = 0.7 });

// Option 3: Load prompt template configuration from a JSON payload
string configPayload = @"{
    ""schema"": 1,
    ""description"": ""Say hello to an AI"",
    ""type"": ""completion"",
    ""completion"": {
        ""max_tokens"": 60,
        ""temperature"": 0.5,
        ""top_p"": 0.0,
        ""presence_penalty"": 0.0,
        ""frequency_penalty"": 0.0
    }
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");
await kernel.RunAsync(func);
```

PR: <https://github.com/microsoft/semantic-kernel/pull/2807>

* Good, SK abstractions contain no references  to OpenAI specific request settings
* Neutral, because anonymous types can be used which allows a developer to pass in properties that may be supported by multiple AI services e.g., `temperature` or combine properties for different AI services e.g., `max_tokens` (OpenAI) and `max_new_tokens` (Oobabooga).
* Bad, because it's not clear to developers what they should pass when creating a semantic function
* Bad, because it's not clear to implementors of a chat/text completion service what they should accept or how to add service specific properties.
* Bad, there is no compiler type checking for code paths where the dynamic argument has not been resolved which will impact code quality. Type issues manifest as `RuntimeBinderException`'s and may be difficult to troubleshoot. Special care needs to be taken with return types e.g., may be necessary to specify an explicit type rather than just `var` again to avoid errors such as `Microsoft.CSharp.RuntimeBinder.RuntimeBinderException : Cannot apply indexing with [] to an expression of type 'object'`

### Use `object` to pass request settings

The `IChatCompletion` interface would look like this:

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        object? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        object? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

The calling pattern is the same as for the `dynamic` case i.e. use either an anonymous type, an AI service specific class e.g., `OpenAIRequestSettings` or load from JSON.

PR: <https://github.com/microsoft/semantic-kernel/pull/2819>

* Good, SK abstractions contain no references  to OpenAI specific request settings
* Neutral, because anonymous types can be used which allows a developer to pass in properties that may be supported by multiple AI services e.g., `temperature` or combine properties for different AI services e.g., `max_tokens` (OpenAI) and `max_new_tokens` (Oobabooga).
* Bad, because it's not clear to developers what they should pass when creating a semantic function
* Bad, because it's not clear to implementors of a chat/text completion service what they should accept or how to add service specific properties.
* Bad, code is needed to perform type checks and explicit casts. The situation is slightly better than for the `dynamic` case.

### Define a base class for AI request settings which all implementations must extend

The `IChatCompletion` interface would look like this:

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

`AIRequestSettings` is defined as follows:

```csharp
public class AIRequestSettings
{
    /// <summary>
    /// Service identifier.
    /// </summary>
    [JsonPropertyName("service_id")]
    [JsonPropertyOrder(1)]
    public string? ServiceId { get; set; } = null;

    /// <summary>
    /// Extra properties
    /// </summary>
    [JsonExtensionData]
    public Dictionary<string, object>? ExtensionData { get; set; }
}
```

Developers would have the following options to specify the requesting settings for a semantic function:

```csharp
// Option 1: Invoke the semantic function and pass an OpenAI specific instance
var result = await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAIRequestSettings() { MaxTokens = 256, Temperature = 0.7 });
Console.WriteLine(result.Result);

// Option 2: Load prompt template configuration from a JSON payload
string configPayload = @"{
    ""schema"": 1,
    ""description"": ""Say hello to an AI"",
    ""type"": ""completion"",
    ""completion"": {
        ""max_tokens"": 60,
        ""temperature"": 0.5,
        ""top_p"": 0.0,
        ""presence_penalty"": 0.0,
        ""frequency_penalty"": 0.0
        }
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

await kernel.RunAsync(func);
```

It would also be possible to use the following pattern:

```csharp
this._summarizeConversationFunction = kernel.CreateSemanticFunction(
    SemanticFunctionConstants.SummarizeConversationDefinition,
    skillName: nameof(ConversationSummarySkill),
    description: "Given a section of a conversation, summarize conversation.",
    requestSettings: new AIRequestSettings()
    {
        ExtensionData = new Dictionary<string, object>()
        {
            { "Temperature", 0.1 },
            { "TopP", 0.5 },
            { "MaxTokens", MaxTokens }
        }
    });

```

The caveat with this pattern is, assuming a more specific implementation of `AIRequestSettings` uses JSON serialization/deserialization to hydrate an instance from the base `AIRequestSettings`, this will only work if all properties are supported by the default JsonConverter e.g.,

* If we have `MyAIRequestSettings` which includes a `Uri` property. The implementation of `MyAIRequestSettings` would make sure to load a URI converter so that it can serialize/deserialize the settings correctly.
* If the settings for `MyAIRequestSettings` are sent to an AI service which relies on the default JsonConverter then a `NotSupportedException` exception will be thrown.

PR: <https://github.com/microsoft/semantic-kernel/pull/2829>

* Good, SK abstractions contain no references  to OpenAI specific request settings
* Good, because it is clear to developers what they should pass when creating a semantic function and it is easy to discover what service specific request setting implementations exist.
* Good, because it is clear to implementors of a chat/text completion service what they should accept and how to extend the base abstraction to add service specific properties.
* Neutral, because `ExtensionData` can be used which allows a developer to pass in properties that may be supported by multiple AI services e.g., `temperature` or combine properties for different AI services e.g., `max_tokens` (OpenAI) and `max_new_tokens` (Oobabooga).
