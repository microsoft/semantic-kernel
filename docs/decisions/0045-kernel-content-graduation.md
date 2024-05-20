---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2024-05-02
deciders: rogerbarreto, markwallace-microsoft, sergeymenkshi, dmytrostruk, sergeymenshik, westey-m, matthewbolanos
consulted: stephentoub
---

# Kernel Content Types Graduation

## Context and Problem Statement

Currently, we have many Content Types in expermental state and this ADR will give some options on how to graduate them to stable state.

## Decision Drivers

- No breaking changes
- Simple approach, minimal complexity
- Allow extensibility
- Concise and clear

## BinaryContent Graduation

Currently Experimental for OpenAIFileService

Encouraged to be used as a content for types that aren't specific. Similar to "octet-stream" in mime types.

> The MIME type for octet-stream, which is used for arbitrary binary data or a stream of bytes that doesn't fit any other more specific MIME type, is application/octet-stream. This MIME type is often used as a default or fallback type, indicating that the file should be treated as pure binary data.

This content works for both deferred (stream factory) and non-deferred content (byte array).

#### Current

```csharp
public class BinaryContent : KernelContent
{
    public ReadOnlyMemory<byte>? Content { get; set; }
    public async Task<Stream> GetStreamAsync()
    public async Task<ReadOnlyMemory<byte>> GetContentAsync()

    ctor(ReadOnlyMemory<byte>? content = null)
    ctor(Func<Task<Stream>> streamProvider)
}
```

#### Proposed

- No Content property (This can clash and be misleading when specialized Binary content types are used)
- No GetContentAsync method (This can clash and be misleading when specialized Binary content types are used)
- Add GetBytesAsync method (To retrieve the content as byte array)
- Add `IsRetrievable` property (To indicate if the content can be retrieved as bytes or stream)
- Add Empty ctor for non-retrievable content
- Add Lazy retrieval for `bytes` and `stream`

**`IsRetrievable`** was selected over `IsExternal`|`IsReferenced` as a streamProvider can be provided (by the connector) to retrieve the content lazily regardless of the content being external or not.

Attempting to get the content as bytes or stream when `IsRetrievable` is false will throw `KernelException("Content is not retrievable")`

```csharp
public class BinaryContent : KernelContent
{
    public async Task<ReadOnlyMemory<byte>>? GetBytesAsync()
    public async Task<Stream> GetStreamAsync()
    bool IsRetrievable { get; } // Indicates if the content can be retrieved as bytes or stream (false for external content that requires customer to handle retrieval)

    ctor(ReadOnlyMemory<byte> bytes) => this(() => Task.FromResult(bytes)) // Shortcut for byte array content
    ctor(Func<Task<ReadOnlyMemory<byte>>> bytesProvider) // Lazy byte array content
    ctor(Func<Task<Stream>> streamProvider) // Lazy stream content
    ctor() // Empty ctor for non-retrievable content
}
```

Pros:

- Clearer API
- Open for extension
  - No `Content` property to clash with specialized Binary content types
  - No `GetContentAsync` method to clash with specialized Binary content types
- `IsRetrievable` will clearly identify if the content can be retrieved as `bytes` or `stream`
- Allow for lazy retrieval of content on both `bytes` and `stream` types

Cons:

- Breaking change for experimental `BinaryContent` consumers

### Specialization Examples

#### ImageContent

`ImageContent -> BinaryContent -> KernelContent`

Not all `ImageContent`s have retriveable `BinaryContent` for scenarios like this the `ImageContent` can be created with a `Uri` and `IsRetrievable` will be false like in the example below.

```csharp
public class ImageContent : BinaryContent
{
    // ... Image specific properties ...
    Uri? Uri => BuildUri(); // Dinamically build the Uri based on how the image was created

    // Inheritance - Retrievable image content
    ctor(ReadOnlyMemory<byte>? content = null) : base(content)
    ctor(Func<Task<Stream>> streamProvider) : base(streamProvider)

    // Specialized - Non-Retrievable image content
    ctor(Uri uri) : base()
}
```

#### FileContent

⚠️ Not in the scope of this ADR (Will be in new contents ADR)

`FileContent` as a `KernelContent` decoration for file specific content information.

```csharp
public class FileContent : KernelContent
{
    // More file specific properties ...
    public string FileName { get; set; }

    // Reference to the binary content
    public MimeType => Content.MimeType;
    public Metadata => Content.Metadata;

    // Retrievable binary file content
    public BinaryContent Content { get; set; }

    ctor(KernelContent content, string fileName, string mimeType)
}

```

## ImageContent Graduation

⚠️ Currently this is experimental, breaking changes needed.

⚠️ Can be graduated to stable state with potential benefits.

#### Current

- Has two properties `Uri` and `Data` that are mutually exclusive.
- Is not a `BinaryContent` type
- Don't support `Stream` type.
- Don't support lazy retrieval.
- Don't have a clear way to indicate if the content is retrievable.

```csharp
public class ImageContent : KernelContent
{
    Uri? Uri { get; set; }
    public ReadOnlyMemory<byte>? Data { get; set; }

    ctor(ReadOnlyMemory<byte>? data)
    ctor(Uri uri)
    ctor()
}
```

#### Proposed

As already shown in the `BinaryContent` section examples, the `ImageContent` can be graduated to be a `BinaryContent` specialization with `Uri` property as a dynamic property.

```csharp
public class ImageContent : BinaryContent
{
    // ... Image specific properties ...
    Uri? Uri => BuildUri(); // Dinamically build the Uri
    // OR / AND
    Task<Uri>? GetUriAsync() => BuildUriAsync(); // Dinamically build the Uri for lazy loading scenarios

    // Retrievable image content
    ctor(ReadOnlyMemory<byte> bytes) : base(bytes)
    ctor(Funv<Task<ReadOnlyMemory<byte>> bytesProvider) : base(bytesProvider)
    ctor(Func<Task<Stream>> streamProvider) : base(streamProvider)

    // When Uri is not DataUrl, this will be non-retrievable content
    ctor(Uri uri)
}
```

Pros:

- Can be used as a `BinaryContent` type
- Can be retrieved as bytes or stream
- Cabnbe lazily retrieved
- Uri is a dynamic property, no more mutually exclusive `Uri` or `Data` properties
- `IsRetrievable` will clearly identify if the content can be retrieved as `bytes`, `stream` or `DataUri`.
- Creating with a non DataUri in the constructor will make it non-retrievable

Cons:

- ⚠️ Breaking change for `ImageContent` consumers

## AudioContent Graduation

Similar to `ImageContent` proposal `AudioContent` can be graduated to be a `BinaryContent` specialization with `Uri` as a dynamic property.

#### Current

- Has no support for referenced `Uri` audio content.
- Is not a `BinaryContent` type
- Don't support `Stream` type.
- Don't support lazy retrieval.
- Don't have a clear way to indicate if the content is retrievable.

```csharp
public class AudioContent : KernelContent
{
    public ReadOnlyMemory<byte>? Data { get; set; }

    ctor(ReadOnlyMemory<byte>? data)
    ctor()
}
```

#### Proposed

```csharp
public class AudioContent : BinaryContent
{
    // ... Audio specific properties ...
    Uri? Uri => BuildUri(); // Dinamically build the Uri or DataUrl for the audio

    // OR / AND
    Task<Uri>? GetUriAsync() => BuildUriAsync(); // Dinamically build the Uri for lazy loading scenarios

    // Retrievable audio content
    ctor(ReadOnlyMemory<byte> bytes) : base(bytes)
    ctor(Funv<Task<ReadOnlyMemory<byte>> bytesProvider) : base(bytesProvider)
    ctor(Func<Task<Stream>> streamProvider) : base(streamProvider)

    // When Uri is not DataUrl, this will be non-retrievable content
    ctor(Uri uri)
}
```

Pros:

- Can be used as a `BinaryContent` type
- Can be retrieved as `bytes`, `stream`, or `DataUri`
- Cab be lazily retrieved
- Uri is a dynamic property
- `IsRetrievable` will clearly identify if the content can be retrieved as `bytes`, `stream` or `DataUri`.
- Creating with a non DataUri in the constructor will make it non-retrievable

Cons:

- Experimental Breaking change for `AudioContent` consumers

## FunctionCallContent Graduation

### Current

No changes needed to current structure.

Potentially we could have a base `FunctionContent` but at the same time is good having those two deriving from `KernelContent` providing a clear separation of concerns.

```csharp
public sealed class FunctionCallContent : KernelContent
{
    public string? Id { get; }
    public string? PluginName { get; }
    public string FunctionName { get; }
    public KernelArguments? Arguments { get; }
    public Exception? Exception { get; init; }

    ctor(string functionName, string? pluginName = null, string? id = null, KernelArguments? arguments = null)

    public async Task<FunctionResultContent> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    public static IEnumerable<FunctionCallContent> GetFunctionCalls(ChatMessageContent messageContent)
}
```

### Problem

It may require a dedicated ADR to the naming standardization between `FunctionCallContent` and `FunctionInvocationContent`, as we have `IAutoFunctionInvocationFilter` naming related for `FunctionCall`.

Those names should be aligned between using `Call` or `Invocation` to avoid confusion, and then we can graduate to stable state.

## FunctinoResultContent Graduation

It may require some changes although the current structure is good.

⚠️ Depending on the decision between `Call` or `Invocation`, consider the same below where reades `Call`.

### Current

- From a purity perspective the `Id` property can lead to confusion as it's not a response Id but a function call Id.
- ctors have different `functionCall` and `functionCallContent` parameter names for same type.

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public string? Id { get; }
    public string? PluginName { get; }
    public string? FunctionName { get; }
    public object? Result { get; }

    ctor(string? functionName = null, string? pluginName = null, string? id = null, object? result = null)
    ctor(FunctionCallContent functionCall, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult result)
}
```

### Proposed - Option 1

- Rename `Id` to `CallId` or `FunctionCallId` to avoid confusion.
- Adjust `ctor` parameters names.

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public string? CallId { get; }
    public string? PluginName { get; }
    public string? FunctionName { get; }
    public object? Result { get; }

    ctor(string? functionName = null, string? pluginName = null, string? callId = null, object? result = null)
    ctor(FunctionCallContent functionCallContent, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult functionResult)
}
```

### Proposed - Option 2

Use composition a have a dedicated CallContent within the `FunctionResultContent`.

Pros:

- `CallContent` has options to invoke a function again from its response which can be handy for some scenarios
- Brings clarity from where the result came from and what is result specific data (root class).
- Knowledge about the arguments used in the call.

Cons:

- Introduce one extra hop to get the `call` details from the result.

```csharp
public sealed class FunctionResultContent : KernelContent
{
    public FunctionCallContent CallContent { get; }
    public object? Result { get; }

    ctor(FunctionCallContent functionCallContent, object? result = null)
    ctor(FunctionCallContent functionCallContent, FunctionResult functionResult)
}
```

## FileReferenceContent + AnnotationContent

Those two contents were added to `SemanticKernel.Abstractions` due to Serialization convenience but are very specific to **OpenAI Assistant API** and should be into `SemanticKernel.Agents.OpenAI` and keep experimental for now.

```csharp
#pragma warning disable SKEXP0110
[JsonDerivedType(typeof(AnnotationContent), typeDiscriminator: nameof(AnnotationContent))]
[JsonDerivedType(typeof(FileReferenceContent), typeDiscriminator: nameof(FileReferenceContent))]
#pragma warning disable SKEXP0110
public abstract class KernelContent { ... }
```

This coupling should not be encouraged for other packages that specialize the `KernelContent` types.

### Solution - Usage of [JsonConverter](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/converters-how-to?pivots=dotnet-6-0#registration-sample---jsonconverter-on-a-type) Annotations

Creation of a dedicated `JsonConverter` helper into the `Agents.OpenAI` project to handle the serialization and deserialization of those types.

Annotate those Content types with `[JsonConverter(typeof(KernelContentConverter))]` attribute to indicate the `JsonConverter` to be used.

### Agents.OpenAI's JsonConverter Example

```csharp
public class KernelContentConverter : JsonConverter<KernelContent>
{
    public override KernelContent Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        using (var jsonDoc = JsonDocument.ParseValue(ref reader))
        {
            var root = jsonDoc.RootElement;
            var typeDiscriminator = root.GetProperty("TypeDiscriminator").GetString();
            switch (typeDiscriminator)
            {
                case nameof(AnnotationContent):
                    return JsonSerializer.Deserialize<AnnotationContent>(root.GetRawText(), options);
                case nameof(FileReferenceContent):
                    return JsonSerializer.Deserialize<FileReferenceContent>(root.GetRawText(), options);
                default:
                    throw new NotSupportedException($"Type discriminator '{typeDiscriminator}' is not supported.");
            }
        }
    }

    public override void Write(Utf8JsonWriter writer, KernelContent value, JsonSerializerOptions options)
    {
        JsonSerializer.Serialize(writer, value, value.GetType(), options);
    }
}

[JsonConverter(typeof(KernelContentConverter))]
public class FileReferenceContent : KernelContent
{
    public string FileId { get; init; } = string.Empty;
    ctor()
    ctor(string fileId, ...)
}

[JsonConverter(typeof(KernelContentConverter))]
public class AnnotationContent : KernelContent
{
    public string? FileId { get; init; }
    public string? Quote { get; init; }
    public int StartIndex { get; init; }
    public int EndIndex { get; init; }
    public ctor()
    public ctor(...)
}
```

## Decision Outcome

- `BinaryContent`: TBD
- `ImageContent`: TBD
- `AudioContent`: TBD
- `FunctionCallContent`: Graduate as is.
- `FunctionResultContent`: Change `Id` to `CallId`.
- `FileReferenceContent` and `AnnotationContent`: No changes, continue as experimental.
