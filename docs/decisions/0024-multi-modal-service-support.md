---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-11-27
deciders: rogerbarreto,markwallace-microsoft,SergeyMenshykh
consulted:
informed:
---

# Streaming Capability for Kernel and Functions usage - Phase 1

## Context and Problem Statement

## Decision Drivers

1. The sk developer should be able to get use different prompt functions using different models and providers, without having to know the details of each model.

2. The sk developer should have a consistent way to get the results from a function, regardless of the model used.

## Out of Scope

### Generic Abstractions

## Services / Connectors

All connectors will have one implementation per modality/model.

Each provider will provide its unique Id for the modality supported, which can be used by the ServiceSelector if a `ProviderId` is defined in the `PromptModel`.

Examples

| Modality      | ProviderId                              | Connector Class          |
| ------------- | --------------------------------------- | ------------------------ |
| Chat to Text  | OpenAI.ChatCompletion                   | ChatCompletionAIService  |
| Text to Image | OpenAI.Dalle3                           | Dalle3AIService          |
| Text to Audio | Azure.CognitiveServices.SpeechSynthesis | SpeechSynthesisAIService |
| Text to Video | Azure.CognitiveServices.VideoIndexer    | VideoIndexerAIService    |
| Text to Text  | OpenAI.TextCompletion                   | TextCompletionAIService  |
| Text to Text  | HuggingFace.TextCompletion              | TextCompletionAIService  |

## Default Service Abstractions (SemanticKernel.Abstractions)

Main abstractions that can be used directly or by the kernel and the functions to consume any AI Models regardless of the modality.

```csharp

public interface IAIService
{
    ...

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(Kernel kernel, ...);
    FunctionResult<T> GetContentAsync<T>(Kernel kernel, ...);
}

```

Extensions to the IAIService to provide a more friendly API to the developer.

```csharp

public static class IAIServiceExtensions
{
    IAsyncEnumerable<StreamingContent> GetStreamingContentAsync(this IAIService service, Kernel kernel, ...);
    FunctionResult<CompleteContent> GetContentAsync(this IAIService service, Kernel kernel, ...);
}

```

### Content Abstractions

Similar to the current `StreamingContent` abstraction, the abstractions below will be used to represent non-streaming (`CompleteContent`) contents returned by the models.

### For content abstractions we have some options:

#### Option 1 - (Shallow inheritance)

This approach suggest that the majority of the specializations will rely on the `CompleteContent<T>` abstraction, and the same Content property will be used to get the actual content, regardless of the type.

Main abstraction for any content type

```csharp
abstract class CompleteContent<T>
{
	public abstract T Content  { get; } // The actual content
	public object InnerContent  { get; } // (Breaking glass)
	public Dictionary<string, object> Metadata  { get; }

    public CompleteContent(object innerContent, Dictionary<string, object>? metadata = null)
    {
        Content = content;
        InnerContent = innerContent;
        Metadata = metadata ?? new();
    }
}
```

Interface abstraction to flag contents that actually are referenced by a URL.

```csharp
interface IReferenceContent // : ContentBase<string> If we want to enforce the string type for referenced contents.
{
	public string Url { get; }
}
```

When executing a method function, the result will be wrapped in a `MethodContent<T>` where T is the type returned by the method.

```csharp
class MethodContent<T> : CompleteContent<T>
{
    public override T Content => this._content;

    public MethodContent(T content) : base(content)
    {
        this._content = content;
    }
}
```

Most raw class, normally can be used for streaming any content´

```csharp
public class BinaryContent : ContentBase<byte[]>
{
string Format { get; }
byte[] Content
}

public class TextContent : ContentBase<string>
{
public string Content
}

public class AudioContent<T> : ContentBase<T>
{
public string Format { get; } // (Mp3, Wav, Wma)
string? Title
TimeSpan? Length
}

public class VideoContent<T> : ContentBase<T>
{
public string Format { get; } // (Mp4, Avi, Wmv)
string? Title
TimeSpan? Length
int? FramesPerSecond
int? Width
int? Height
}

public class ImageContent<T> : ContentBase<T>
{
public string Format { get; } // (Jpg, Png, Gif, Bmp, Tiff, Svg)
public string? Title { get; }
public int? Width { get; }
public int? Height { get; }
}

```

## Specialized Abstractions: (SemanticKernel.Abstractions)

Used in some scenarios where the above abstractions are not enough to represent the content. Like Chat, Json, etc.

```csharp

public class JsonContent : ContentBase<JsonElement>
{
}

public class ChatContent : ContentBase<string>
{
	public string Role
}

```

## Custom Specializations (Connectors):

```csharp

// OpenAI Connector Examples
public sealed class OpenAIChatContent : ChatContent
{
	TooCalls[] TooCalls

	private class ToolCall {
		public int Index { get; }
		public string Id { get; }
		string Type  { get; }  // The type of the tool. Currently, only function is supported.
    }

    private class Function {
        public string Name { get; } // The name of the function to call.
        public string Arguments { get; } // The arguments to call the function with, as generated by the model in JSON format
    }
}

public sealed class OpenAIImageContent : ImageContent<string>, IReferenceContent
{
    public string Url { get; }
    public string B64Json { get; }
    public string RevisedPrompt { get; }
}

// Document Model Connector Examples
public sealed class CsvDocumentContent : ContentBase<MyCSV>
{
	MyCSV Content { get; }
}

public sealed class MarkdownContent : TextContent
{
    bool Valid { get; }
}

public sealed class HtmlContent : ContentBase<HtmlElement>
{
    HtmlElement Content { get; }
}

public sealed class Swagger/OpenAPIContent : JsonContent
{
    string Definition { get; }
    Endpoints[] Endpoints { get; }
}
```

## How handle the current contents in `FunctionResults`?

Functions results will support by default the `CompleteContent` abstraction.

````csharp
// Classic Function result will be a MethodContent<object>
public class FunctionResult : MethodContent<object> {
    // ... extra properties IsCancelled, IsSkipped, etc

    object Content => this._value;

    [Obsolete("Use Content property instead")]
    T GetValue<T>() => (T)this.Content;

    FunctionResult(object value) : base(value) {
        this._value = value;
    }

    private object _value;
}

// Generic Function result (Default for all InvokeAsync<T> / RunAsync<T>)
public class FunctionResult<T> : CompleteContent<T> {
    // ... extra properties IsCancelled, IsSkipped, etc

    public CompleteContent<T> Content => this._completeContent.Content;

    FunctionResult(CompleteContent<T> completeContent) : base(completeContent.Content) {
        this._completeContent = completeContent;
    }

    private CompleteContent<T> _completeContent;
}


```csharp
public static class FunctionResultExtensions {

    ...
    public static CompleteContent GetValue(this FunctionResult functionResult) {
        this.GetValue<CompleteContent>();
    }
}

````

## How to handle multiple choices in a full content?

### Option 1 - Always gives back multiple elements (IReadOnlyList/IReadOnlyCollection/IEnumerable) (Same behavior as StreamingContent)

```csharp
FunctionResult<IEnumerable<T>> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
content = result.First().Content;
// OR
FunctionResult<ICollection<T>> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
content = result[0].Content;
// OR
FunctionResult<IList<T>> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
content = result[0].Content;

var singleResult = await kernel.RunSingleAsync<T>(function, variables, cancellationToken);
content = singleResult.Content
```

Pros:

- Always same result type, simplicity on the caller side.

Downside:

- Majority of single element results will require `First()` or `[0]` to get the value.
- A new extension method would be needed to mitigate which would add a new API. Like `kernel.RunSingleAsync<T>`

### Option 2 - Always gives back a single element

This will always give back one element, if multiple are requested, this method will throw an exception. A multiple specific API would be needed to get multiple results.

```csharp
FunctionResult<T> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
content = result.Content;

var multipleResult = await kernel.RunMultipleAsync<T>(function, variables, cancellationToken);
content = multipleResult[0].Content
```

Pros:

- Always same result type.
- Minimal friction to current status quo.
- Simplicity on the caller side.

Cons:

- Differs from the streaming API behavior which will always give back a list of elements.
- A new API (**cannot be an extension**) method would be needed to mitigate the Single result limitation. Something like: `kernel.RunMultipleAsync<T>()`

### Option 3 - Gives back what you asked

```csharp
FunctionResult<T> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
content = result.Content;
// AND
FunctionResult<T[]> result = await kernel.RunAsync<T[]>(function, variables, cancellationToken);
content = result[0].Content;
// AND
FunctionResult<IList<T>> result = await kernel.RunAsync<IList<T>>(function, variables, cancellationToken);
content = result[0].Content;


```

Pros:

- No conversion is needed
- Flexibility to the caller to choose what he wants (Works well for deterministic functions)

Cons:

- When implementing non deterministic logic the caller will need to do know if multiple results will be returned to use the correct signature.

### Option 3 - Gives back a list when multiple and One element when one?

Returns a `FunctionResult<object>` which in reality can be a `FunctionResult<T>` when the result is a single content or `FunctionResult<IEnumerable<T>>` when there are multiple contents.

```csharp
FunctionResult<object> result = await kernel.RunAsync<T>(function, variables, cancellationToken);
if (result.GetType().IsAssignableTo(typeof(FunctionResult<IEnumerable<T>>)))
    content = ((FunctionResult<IEnumerable<T>>)result).First().Content;
else
    content = ((FunctionResult<T>)result).Content;
```

Pros:

- Abstract friendly API, one signature for both cases.

Downside:

- Always requires a cast to get the value.
- Extra verbosity and complexity on the caller side to know if the result is a list or not.

### Option 4 - One content with multiple inner choices?

Returns the classic Function Result with a Method `GetChoices<T>` to get the choice at the given index, if not provided the first choice will be returned.

```csharp

// If you provide an IEnumerable<T> as generic parameter, the result will be a FunctionResult<IEnumerable<T>>
FunctionResult result = await kernel.RunAsync(function, variables, cancellationToken);
var content = result.GetChoices<T>(int index = default).Content;
```
