---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-11-27
deciders: rogerbarreto,markwallace-microsoft,SergeyMenshykh
consulted:
informed:
---

# Multi Modality Services & Content Support

## Context and Problem Statement

## Decision Drivers

1. A sk developer should be able to use different prompt functions against different models and service providers without having to know the specific details of each model.

2. A sk developer should be able to get results from a function in a consistent, simple and easy way regardless of the model used.

### Index

- `AIService` Abstractions
- `Content` Abstractions
- `FunctionResult` Abstractions

## Out of Scope

- TBC

### Generic Abstractions

## `AIService` Abstractions

Main `AIService` abstractions that can be used directly by the kernel execute prompt functions with any AI Models regardless of the modality.

`IAIService` interface become the main abstraction for modality/model support.

All connectors will have one or multiple services implementing `IAIService` for each modality/model they support.

[ ] Suggestion: Each provider can also have its unique `ProviderModalityId` for the modality supported which can be used by the `ServiceSelector` to select the correct service to use.

### How connectors can implement the new `IAIService` abstraction:

| Modality       | Connector   | ProviderModalityId            | Connector Class              | ModelId                      |
| -------------- | ----------- | ----------------------------- | ---------------------------- | ---------------------------- |
| Text to Text   | AzureOpenAI | OpenAI.Text.Completion        | TextCompletionAIService      | text-davinci-003             |
| Chat to Chat   | AzureOpenAI | OpenAI.Chat.Completion        | ChatCompletionAIService      | gpt-3.5-turbo, gpt-4         |
| Chat to Chat   | AzureOpenAI | AzureOpenAI.Chat.Completion   | AzureChatCompletionAIService | gpt-4.5-turbo, gpt-4         |
| Text to Image  | AzureOpenAI | OpenAI.Image.Creation         | Dalle3AIService              | dalle3                       |
| Text to Audio  | AzureOpenAI | OpenAI.Audio.Speaking         | TextToAudioAIService         | tts-1, tts-2                 |
| Audio to Text  | AzureOpenAI | OpenAI.Audio.Transcribing     | AudioToTextAIService         | whisper-1                    |
| Text to Image  | MidJourney  | MidJourney.Image.Creation     | MidJourneyV5AIService        | V4, V4.1, V5                 |
| Image to Image | MidJourney  | MidJourney.Image.Blending     | MidJourneyBlendAIService     | V4, V4.1, V5                 |
| Text to Text   | HuggingFace | HuggingFace.Text.Completion   | TextCompletionAIService      | meta-llama/Llama-2-7b-hf     |
| Text to Image  | HuggingFace | HuggingFace.Image.Creation    | HuggingFaceImageAIService    | stabilityai/stable-diffusion |
| Text to Text   | Amazon      | AmazonBedrock.Text.Completion | TextCompletionAIService      | claude, amazon-titan         |
| Text to Image  | Amazon      | AmazonBedrock.Image.Creation  | TextCompletionAIService      | stable-diffusion             |

Interfaces like `ITextCompletion`, `IChatCompletion`, `ImageGeneration` will be removed and current implementations will now be using a `IAIService` abstraction returned by the Service Selector.

### Target User experience

Before:

```csharp
 var dallE = kernel.GetService<IImageGeneration>();
 var image = await dallE.GenerateImageAsync("A cute baby sea otter", 256, 256);
```

After:

```csharp
 var dallE = kernel.GetService<IAIService>("dalle3");
 var settings = new OpenAIImageCreationSettings { Width = 256, Height = 256 };
 var image = await dallE.GetContentAsync<ImageContent>(kernel, "A cute baby sea otter", settings);
```

#### `IAIService` Example

```csharp
public interface IAIService
{
    string ProviderId { get; }

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(Kernel kernel, ...);
    FunctionResult<T> GetContentAsync<T>(Kernel kernel, ...);
}
```

Usage:

```csharp
var chatService = kernel.GetService<IAIService>("gpt-4");

// Chat Or TextCompletion

// non streaming
var myResult = chatService.GetContentAsync<CompleteContent>(kernel, ...);
Console.WriteLine(myResult.Content);

// streaming
await foreach (var content in chatService.GetStreamingContentAsync<StreamingContent>(kernel, ...))
{
    Console.WriteLine(content);
}

// Image generation
var dallE = kernel.GetService<IAIService>("dalle3");
var settings = new OpenAIImageCreationSettings { Width = 256, Height = 256 };
var imageContent = await dallE.GetContentAsync<ImageContent>(kernel, "A cute baby sea otter", settings);
```

#### Convenience Extensions to the `IAIService`

Those are convenient default extensions that can expose the `Content` abstractions directly without having to specify the generic type.

_All the AI Services will support and return a specialized `CompleteContent` abstraction._

```csharp
public static class IAIServiceExtensions
{
    IAsyncEnumerable<StreamingContent> GetStreamingContentAsync(this IAIService service, Kernel kernel, ...);
    FunctionResult<CompleteContent> GetContentAsync(this IAIService service, Kernel kernel, ...);
}
```

Usage: (Without generics)

```csharp
var chatService = kernel.GetService<IAIService>("gpt-4");
var myResult = chatService.GetContentAsync(kernel, ...);
Console.WriteLine(myResult.Content);
```

### **Content** Abstractions

Similar on how streaming abstractions work, the abstractions below will be used to represent non-streaming contents returned by the models.

#### Option 1 - (Shallow inheritance)

In this approach the majority of the specializations will rely on the `CompleteContent<T>` abstraction, and the same Content property will be used to get the actual content, regardless of the type.

### Pros

- All Content will have one property `Content` which will be generic to the type of the content you expect.
- The caller needs to know what is the type of the content he is expecting, to be able to get it from the method result.

Usage:

```csharp
var myResult = chatService.GetContentAsync<ChatContent>(kernel, ...);
foreach(var message in myResult.Content) {
    Console.WriteLine(message.Role + ": " + message.Content);
}
```

#### High level abstractions

```csharp
abstract class CompleteContent<T>
{
	abstract T Content  { get; } // The actual content
	object InnerContent  { get; } // (Breaking glass)
	Dictionary<string, object> Metadata  { get; }

    CompleteContent(object innerContent, Dictionary<string, object>? metadata = null)
    {
        Content = content;
        InnerContent = innerContent;
        Metadata = metadata ?? new();
    }
}
```

`KernelMethodFunction`s results will be wrapped in a `MethodContent<T>` where T is the type returned by the method.

```csharp
class MethodContent<T> : CompleteContent<T>
{
    override T Content { get; }

    MethodContent(T content) : base(content)
    {
        this.Content = content;
    }
}
```

Octect Type Content (Generaly for binary content, files, executables, etc)

```csharp
class BinaryContent : ContentBase<byte[]>
{
    string Format { get; }
    byte[] Content { get; }

    //ctor
}
```

#### Low level abstractions (Content specific types)

Text Type Content (Generaly for text content, strings, etc)

```csharp
class TextContent : ContentBase<string>
{
    Encoding Format { get; } = Encoding.UTF8;
    string Content { get; }

    //ctor
}
```

Audio content

```csharp
class AudioContent<T> : ContentBase<T>
{
    string Format { get; } // (Mp3, Wav, Wma)
    string? Title { get; }
    TimeSpan? Length { get; }
}
```

Video content

```csharp
class VideoContent<T> : ContentBase<T>
{
    string Format { get; } // (Mp4, Avi, Wmv)
    string? Title
    TimeSpan? Length
    int? FramesPerSecond
    int? Width
    int? Height
}
```

Image content

```csharp
class ImageContent<T> : ContentBase<T>
{
    string Format { get; } // (Jpg, Png, Gif, Bmp, Tiff, Svg)
    string? Title { get; }
    int? Width { get; }
    int? Height { get; }
}
```

Json content

```csharp
class JsonContent : ContentBase<JsonElement>
{
}
```

Chat content (Promoted to abstractions as it became the most used content type with OpenAI)

```csharp
class ChatContent : ContentBase<ChatHistory>
{
}
```

#### Connector (Specialized) Abstractions:

Used in scenarios where the above abstractions are not enough to represent the content. Like OpenAIChat, Swagger/OpenAPI, etc.

#### OpenAI Connector Examples

```csharp
public sealed class OpenAIChatContent : ChatContent
{
	ICollection<ToolCalls> ToolCalls { get; }

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

### Option 2 - (Deep inheritance)

```csharp
abstract class CompleteContent
{
	public object RawContent  { get; } // The actual content
	public Dictionary<string, object> Metadata  { get; }

    public CompleteContent(object rawContent, Dictionary<string, object>? metadata = null)
    {
        RawContent = rawContent;
        Metadata = metadata ?? new();
    }

    public T GetContent<T>() => (T)this.RawContent;
}

interface IReferenceContent // : ContentBase<string> If we want to enforce the string type for referenced contents.
{
    public string Url { get; }
}

class MethodContent : CompleteContent
{
    /// .. MethodContent specific properties
    public MethodContent(T content) : base(content)
    {
        this._content = content;
    }

    public T GetContent<T> => (T)this.RawContent;
    public override object RawContent => this._content;
}

public class BinaryContent : CompleteContent
{
    public string Format { get; }
    public byte[] BinaryContent { get; }

    public BinaryContent(byte[] content, string format, Dictionary<string, object>? metadata = null)
    : base(content, metadata)
    {
        Format = format;
        this.BinaryContent = content;
    }
}

public class ImageContent : BinaryContent
{
    public string Format { get; }
    public int Width { get; }
    public int Height { get; }
    public byte[] ImageContent => base.BinaryContent;

    public ImageContent(byte[] content, string format, Dictionary<string, object>? metadata = null)
    : base(content, metadata)
    {
        Format = format;
        this.BinaryContent = content;
    }
}

public class TextContent : BinaryContent
{
    public Encoding Format { get; }
    public string TextContent { get; }

    // By default we will use UTF8 when providing string content
    public TextContent(string content, Dictionary<string, object>? metadata = null)
    : base(Encoding.UTF8.GetBytes(content), metadata)
    {
        this.Format = Encoding.UTF8;
        this.TextContent = content;
    }

    public TextContent(byte[] content, Encoding format, Dictionary<string, object>? metadata = null) : base(content, metadata)
    {
        this.Format = format;
        this.TextContent = format.GetString(content);
    }
}

public class JsonContent : TextContent
{
    JsonElement JsonContent { get; }

    public JsonContent(string content, Dictionary<string, object>? metadata = null)
    : base(content, metadata)
    {
        this.JsonContent = JsonSerializer.Deserialize<JsonElement>(content);
    }
}

public class ChatContent : JsonContent
{
    public virtual IReadOnlyList<ChatMessage> Messages { get; }

    public ChatContent(IList<ChatMessage> messages, Dictionary<string, object>? metadata = null)
    : base(content, metadata)
    {
        this.Messages = messages.ToList();
    }

    public JsonChatContent(object content, Dictionary<string, object>? metadata = null))
    {}

    public record ChatMessage (string Role, string Content);
}

public class OpenAIChatContent : ChatContent
{

    public OpenAIChatContent(string serializedOpenAIChat, Dictionary<string, object>? metadata = null)
    : base(serializedOpenAIChat, metadata)
    {

    }

    public record ChatMessage (string Role, string Content);
}

public class Swagger/OpenAPIContent : JsonContent
{
    string Definition { get; }
    Endpoints[] Endpoints { get; }

    public Swagger/OpenAPIContent(string content, Dictionary<string, object>? metadata = null)
    : base(content, metadata)
    {
        this.Definition = base.JsonContent.GetProperty("definition").GetString();
        this.Endpoints = base.JsonContent.GetProperty("endpoints").EnumerateArray().Select(e => new Endpoint(e)).ToArray();
    }
}

```

#### Useful interfaces

To flag contents that actually are created and referenced by a URL.

```csharp
interface IReferencedContent
{
	public string ContentUrl { get; }
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

### Option 4 - Gives back a list when multiple and One element when one?

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

### Option 5 - One content with multiple inner choices?

Returns the classic Function Result with a Method `GetChoices<T>` to get the choice at the given index, if not provided the first choice will be returned.

```csharp

// If you provide an IEnumerable<T> as generic parameter, the result will be a FunctionResult<IEnumerable<T>>
FunctionResult result = await kernel.RunAsync(function, variables, cancellationToken);
var content = result.GetChoices<T>(int index = default).Content;
```
