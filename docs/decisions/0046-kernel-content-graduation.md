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

Currently, we have many Content Types in experimental state and this ADR will give some options on how to graduate them to stable state.

## Decision Drivers

- No breaking changes
- Simple approach, minimal complexity
- Allow extensibility
- Concise and clear

## BinaryContent Graduation

This content should be by content specializations or directly for types that aren't specific, similar to "application/octet-stream" mime type.

> **Application/Octet-Stream** is the MIME used for arbitrary binary data or a stream of bytes that doesn't fit any other more specific MIME type. This MIME type is often used as a default or fallback type, indicating that the file should be treated as pure binary data.

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

```csharp
public class BinaryContent : KernelContent
{
    ReadOnlyMemory<byte>? Data { get; set; }
    Uri? Uri { get; set; }
    string DataUri { get; set; }

    bool CanRead { get; } // Indicates if the content can be read as bytes or data uri

    ctor(Uri? referencedUri)
    ctor(string dataUri)
    // MimeType is not optional but nullable to encourage this information to be passed always when available.
    ctor(ReadOnlyMemory<byte> data, string? mimeType)
    ctor() // Empty ctor for serialization scenarios
}
```

- No Content property (Avoid clashing and/or misleading information if used from a specialized type context)

  i.e:

  - `PdfContent.Content` (Describe the text only information)
  - `PictureContent.Content` (Exposes a `Picture` type)

- Move away from deferred (lazy loaded) content providers, simpler API.
- `GetContentAsync` removal (No more derrefed APIs)
- Added `Data` property as setter and getter for byte array content information.

  Setting this property will override the `DataUri` base64 data part.

- Added `DataUri` property as setter and getter for data uri content information.

  Setting this property will override the `Data` and `MimeType` properties with the current payload details.

- Add `Uri` property for referenced content information. This property is does not accept not a `UriData` and only supports non-data schemes.
- Add `CanRead` property (To indicate if the content can be read using `Data` or `DataUri` properties.)
- Dedicated constructors for Uri, DataUri and ByteArray + MimeType creation.

Pros:

- With no deferred content we have simpler API and a single responsibility for contents.
- Can be written and read in both `Data` or `DataUri` formats.
- Can have a `Uri` reference property, which is common for specialized contexts.
- Fully serializable.
- Data Uri parameters support (serialization included).
- Data Uri and Base64 validation checks
- Data Uri and Data can be dynamically generated
- `CanRead` will clearly identify if the content can be read as `bytes` or `DataUri`.

Cons:

- Breaking change for experimental `BinaryContent` consumers

### Data Uri Parameters

According to [RFC 2397](https://datatracker.ietf.org/doc/html/rfc2397), the data uri scheme supports parameters

Every parameter imported from the data uri will be added to the Metadata dictionary with the "data-uri-parameter-name" as key and its respetive value.

#### Providing a parameterized data uri will include those parameters in the Metadata dictionary.

```csharp
var content = new BinaryContent("data:application/json;parameter1=value1;parameter2=value2;base64,SGVsbG8gV29ybGQ=");
var parameter1 = content.Metadata["data-uri-parameter1"]; // value1
var parameter2 = content.Metadata["data-uri-parameter2"]; // value2
```

#### Deserialization of contents will also include those parameters when getting the DataUri property.

```csharp
var json = """
{
    "metadata":
    {
        "data-uri-parameter1":"value1",
        "data-uri-parameter2":"value2"
    },
    "mimeType":"application/json",
    "data":"SGVsbG8gV29ybGQ="
}
""";
var content = JsonSerializer.Deserialize<BinaryContent>(json);
content.DataUri // "data:application/json;parameter1=value1;parameter2=value2;base64,SGVsbG8gV29ybGQ="
```

### Specialization Examples

#### ImageContent

```csharp
public class ImageContent : BinaryContent
{
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}

public class AudioContent : BinaryContent
{
    ctor(Uri uri)
}
```

Pros:

- Supports data uri large contents
- Allows a binary ImageContent to be created using dataUrl scheme and also be referenced by a Url.
- Supports Data Uri validation

## ImageContent Graduation

⚠️ Currently this is not experimental, breaking changes needed to be graduated to stable state with potential benefits.

### Problems

1. Current `ImageContent` does not derive from `BinaryContent`
2. Has an undesirable behavior allowing the same instance to have distinct `DataUri` and `Data` at the same time.
3. `Uri` property is used for both data uri and referenced uri information
4. `Uri` does not support large language data uri formats.
5. Not clear to the `sk developer` whenever the content is readable or not.

#### Current

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

As already shown in the `BinaryContent` section examples, the `ImageContent` can be graduated to be a `BinaryContent` specialization an inherit all the benefits it brings.

```csharp
public class ImageContent : BinaryContent
{
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}
```

Pros:

- Can be used as a `BinaryContent` type
- Can be written and read in both `Data` or `DataUri` formats.
- Can have a `Uri` dedicated for referenced location.
- Fully serializable.
- Data Uri parameters support (serialization included).
- Data Uri and Base64 validation checks
- Can be retrieved
- Data Uri and Data can be dynamically generated
- `CanRead` will clearly identify if the content can be read as `bytes` or `DataUri`.

Cons:

- ⚠️ Breaking change for `ImageContent` consumers

### ImageContent Breaking Changes

- `Uri` property will be dedicated solely for referenced locations (non-data-uri), attempting to add a `data-uri` format will throw an exception suggesting the usage of the `DataUri` property instead.
- Setting `DataUri` will override the `Data` and `MimeType` properties according with the information provided.
- Attempting to set an invalid `DataUri` will throw an exception.
- Setting `Data` will now override the `DataUri` data part.
- Attempting to serialize an `ImageContent` with data-uri in the `Uri` property will throw an exception.

## AudioContent Graduation

Similar to `ImageContent` proposal `AudioContent` can be graduated to be a `BinaryContent`.

#### Current

1. Current `AudioContent` does not derive support `Uri` referenced location
2. `Uri` property is used for both data uri and referenced uri information
3. `Uri` does not support large language data uri formats.
4. Not clear to the `sk developer` whenever the content is readable or not.

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
    ctor(Uri uri) : base(uri)
    ctor(string dataUri) : base(dataUri)
    ctor(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    ctor() // serialization scenarios
}
```

Pros:

- Can be used as a `BinaryContent` type
- Can be written and read in both `Data` or `DataUri` formats.
- Can have a `Uri` dedicated for referenced location.
- Fully serializable.
- Data Uri parameters support (serialization included).
- Data Uri and Base64 validation checks
- Can be retrieved
- Data Uri and Data can be dynamically generated
- `CanRead` will clearly identify if the content can be read as `bytes` or `DataUri`.

Cons:

- Experimental breaking change for `AudioContent` consumers

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

## FunctionResultContent Graduation

It may require some changes although the current structure is good.

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

- Rename `Id` to `CallId` to avoid confusion.
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

Those two contents were added to `SemanticKernel.Abstractions` due to Serialization convenience but are very specific to **OpenAI Assistant API** and should be kept as Experimental for now.

As a graduation those should be into `SemanticKernel.Agents.OpenAI` following the suggestion below.

```csharp
#pragma warning disable SKEXP0110
[JsonDerivedType(typeof(AnnotationContent), typeDiscriminator: nameof(AnnotationContent))]
[JsonDerivedType(typeof(FileReferenceContent), typeDiscriminator: nameof(FileReferenceContent))]
#pragma warning disable SKEXP0110
public abstract class KernelContent { ... }
```

This coupling should not be encouraged for other packages that have `KernelContent` specializations.

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

- `BinaryContent`: Accepted.
- `ImageContent`: Breaking change accepted with benefits using the `BinaryContent` specialization. No backwards compatibility as the current `ImageContent` behavior is undesirable.
- `AudioContent`: Experimental breaking changes using the `BinaryContent` specialization.
- `FunctionCallContent`: Graduate as is.
- `FunctionResultContent`: Experimental breaking change from property `Id` to `CallId` to avoid confusion regarding being a function call Id or a response id.
- `FileReferenceContent` and `AnnotationContent`: No changes, continue as experimental.
