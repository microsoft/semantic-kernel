---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-11-13
deciders: rogerbarreto,markwallace-microsoft,SergeyMenshykh,dmytrostruk
consulted:
informed:
---

# Streaming Capability for Kernel and Functions usage - Phase 1

## Context and Problem Statement

It is quite common in co-pilot implementations to have a streamlined output of messages from the LLM (large language models)M and currently that is not possible while using ISKFunctions.InvokeAsync or Kernel.RunAsync methods, which enforces users to work around the Kernel and Functions to use `ITextCompletion` and `IChatCompletion` services directly as the only interfaces that currently support streaming.

Currently streaming is a capability that not all providers do support and this as part of our design we try to ensure the services will have the proper abstractions to support streaming not only of text but be open to other types of data like images, audio, video, etc.

Needs to be clear for the sk developer when he is attempting to get streaming data.

## Decision Drivers

1. The sk developer should be able to get streaming data from the Kernel and Functions using Kernel.RunAsync or ISKFunctions.InvokeAsync methods

2. The sk developer should be able to get the data in a generic way, so the Kernel and Functions can be able to stream data of any type, not limited to text.

3. The sk developer when using streaming from a model that does not support streaming should still be able to use it with only one streaming update representing the whole data.

## Out of Scope

- Streaming with plans will not be supported in this phase. Attempting to do so will throw an exception.
- Kernel streaming will not support multiple functions (pipeline).
- Input streaming will not be supported in this phase.
- Post Hook Skipping, Repeat and Cancelling of streaming functions are not supported.

## Considered Options

### Option 1 - Dedicated Streaming Interfaces

Using dedicated streaming interfaces that allow the sk developer to get the streaming data in a generic way, including string, byte array directly from the connector as well as allowing the Kernel and Functions implementations to be able to stream data of any type, not limited to text.

This approach also exposes dedicated interfaces in the kernel and functions to use streaming making it clear to the sk developer what is the type of data being returned in IAsyncEnumerable format.

`ITextCompletion` and `IChatCompletion` will have new APIs to get `byte[]` and `string` streaming data directly as well as the specialized `StreamingContent` return.

The sk developer will be able to specify a generic type to the `Kernel.RunStreamingAsync<T>()` and `ISKFunction.InvokeStreamingAsync<T>` to get the streaming data. If the type is not specified, the Kernel and Functions will return the data as StreamingContent.

If the type is not specified or if the string representation cannot be cast, an exception will be thrown.

If the type specified is `StreamingContent` or another any type supported by the connector no error will be thrown.

## User Experience Goal

```csharp
//(providing the type at as generic parameter)

// Getting a Raw Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingContent as Streaming data from Kernel
await foreach(StreamingContent update in kernel.RunStreamingAsync<StreamingContent>(variables, function))
// OR
await foreach(StreamingContent update in kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}
```

Abstraction class for any stream content, connectors will be responsible to provide the specialized type of `StreamingContent` which will contain the data as well as any metadata related to the streaming result.

```csharp

public abstract class StreamingContent
{
    public abstract int ChoiceIndex { get; }

    /// Returns a string representation of the chunk content
    public abstract override string ToString();

    /// Abstract byte[] representation of the chunk content in a way it could be composed/appended with previous chunk contents.
    /// Depending on the nature of the underlying type, this method may be more efficient than <see cref="ToString"/>.
    public abstract byte[] ToByteArray();

    /// Internal chunk content object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the content chunk content.
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    public object? InnerContent { get; }

    /// The metadata associated with the content.
    public Dictionary<string, object>? Metadata { get; set; }

    /// The current context associated the function call.
    internal SKContext? Context { get; set; }

    /// <param name="innerContent">Inner content object reference</param>
    protected StreamingContent(object? innerContent)
    {
        this.InnerContent = innerContent;
    }
}
```

Specialization example of a StreamingChatContent

```csharp
//
public class StreamingChatContent : StreamingContent
{
    public override int ChoiceIndex { get; }
    public FunctionCall? FunctionCall { get; }
    public string? Content { get; }
    public AuthorRole? Role { get; }
    public string? Name { get; }

    public StreamingChatContent(AzureOpenAIChatMessage chatMessage, int resultIndex) : base(chatMessage)
    {
        this.ChoiceIndex = resultIndex;
        this.FunctionCall = chatMessage.InnerChatMessage?.FunctionCall;
        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role.ToString());
        this.Name = chatMessage.InnerChatMessage?.Name;
    }

    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(this.ToString());
    public override string ToString() => this.Content ?? string.Empty;
}
```

`IChatCompletion` and `ITextCompletion` interfaces will have new APIs to get a generic streaming content data.

```csharp
interface ITextCompletion + IChatCompletion
{
    IAsyncEnumerable<T> GetStreamingContentAsync<T>(...);

    // Throw exception if T is not supported
}

interface IKernel
{
    // Get streaming function content of T
    IAsyncEnumerable<T> RunStreamingAsync<T>(ContextVariables variables, ISKFunction function);
}

interface ISKFunction
{
    // Get streaming function content of T
    IAsyncEnumerable<T> InvokeStreamingAsync<T>(SKContext context);
}
```

## Prompt/Semantic Functions Behavior

When Prompt Functions are invoked using the Streaming API, they will attempt to use the Connectors streaming implementation.
The connector will be responsible to provide the specialized type of `StreamingContent` and even if the underlying backend API don't support streaming the output will be one streamingcontent with the whole data.

## Method/Native Functions Behavior

Method Functions will support `StreamingContent` automatically with as a `StreamingMethodContent` wrapping the object returned in the iterator.

```csharp
public sealed class StreamingMethodContent : StreamingContent
{
    public override int ChoiceIndex => 0;

    /// Method object value that represents the content chunk
    public object Value { get; }

    /// Default implementation
    public override byte[] ToByteArray()
    {
        if (this.Value is byte[])
        {
            // If the method value is byte[] we return it directly
            return (byte[])this.Value;
        }

        // By default if a native value is not byte[] we output the UTF8 string representation of the value
        return Encoding.UTF8.GetBytes(this.Value?.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Value.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingMethodContent"/> class.
    /// </summary>
    /// <param name="innerContent">Underlying object that represents the chunk</param>
    public StreamingMethodContent(object innerContent) : base(innerContent)
    {
        this.Value = innerContent;
    }
}
```

If a MethodFunction is returning an `IAsyncEnumerable` each enumerable result will be automatically wrapped in the `StreamingMethodContent` keeping the streaming behavior and the overall abstraction consistent.

When a MethodFunction is not an `IAsyncEnumerable`, the complete result will be wrapped in a `StreamingMethodContent` and will be returned as a single item.

## Pros

1. All the User Experience Goal section options will be possible.
2. Kernel and Functions implementations will be able to stream data of any type, not limited to text
3. The sk developer will be able to provide the streaming content type it expects from the `GetStreamingContentAsync<T>` method.
4. Sk developer will be able to get streaming from the Kernel, Functions and Connectors with the same result type.

## Cons

1. If the sk developer wants to use the specialized type of `StreamingContent` he will need to know what the connector is being used to use the correct **StreamingContent extension method** or to provide directly type in `<T>`.
2. Connectors will have greater responsibility to support the correct special types of `StreamingContent`.

### Option 2 - Dedicated Streaming Interfaces (Returning a Class)

All changes from option 1 with the small difference below:

- The Kernel and SKFunction streaming APIs interfaces will return `StreamingFunctionResult<T>` which also implements `IAsyncEnumerable<T>`
- Connectors streaming APIs interfaces will return `StreamingConnectorContent<T>` which also implements `IAsyncEnumerable<T>`

The `StreamingConnectorContent` class is needed for connectors as one way to pass any information relative to the request and not the chunk that can be used by the functions to fill `StreamingFunctionResult` metadata.

## User Experience Goal

Option 2 Biggest benefit:

```csharp
// When the caller needs to know more about the streaming he can get the result reference before starting the streaming.
var streamingResult = await kernel.RunStreamingAsync(function);
// Do something with streamingResult properties

// Consuming the streamingResult requires an extra await:
await foreach(StreamingContent chunk content in await streamingResult)
```

Using the other operations will be quite similar (only needing an extra `await` to get the iterator)

```csharp
// Getting a Raw Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingContent as Streaming data from Kernel
await foreach(StreamingContent update in await kernel.RunStreamingAsync<StreamingContent>(variables, function))
// OR
await foreach(StreamingContent update in await kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}

```

StreamingConnectorResult is a class that can store information regarding the result before the stream is consumed as well as any underlying object (breaking glass) that the stream consumes at the connector level.

```csharp

public sealed class StreamingConnectorResult<T> : IAsyncEnumerable<T>
{
    private readonly IAsyncEnumerable<T> _StreamingContentource;

    public object? InnerResult { get; private set; } = null;

    public StreamingConnectorResult(Func<IAsyncEnumerable<T>> streamingReference, object? innerConnectorResult)
    {
        this._StreamingContentource = streamingReference.Invoke();
        this.InnerResult = innerConnectorResult;
    }
}

interface ITextCompletion + IChatCompletion
{
    Task<StreamingConnectorResult<T>> GetStreamingContentAsync<T>();
    // Throw exception if T is not supported
    // Initially connectors
}
```

StreamingFunctionResult is a class that can store information regarding the result before the stream is consumed as well as any underlying object (breaking glass) that the stream consumes from Kernel and SKFunctions.

```csharp
public sealed class StreamingFunctionResult<T> : IAsyncEnumerable<T>
{
    internal Dictionary<string, object>? _metadata;
    private readonly IAsyncEnumerable<T> _streamingResult;

    public string FunctionName { get; internal set; }
    public Dictionary<string, object> Metadata { get; internal set; }

    /// <summary>
    /// Internal object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result.
    /// </summary>
    public object? InnerResult { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="SKContext"/> used by the function.
    /// </summary>
    internal SKContext Context { get; private set; }

    public StreamingFunctionResult(string functionName, SKContext context, Func<IAsyncEnumerable<T>> streamingResult, object? innerFunctionResult)
    {
        this.FunctionName = functionName;
        this.Context = context;
        this._streamingResult = streamingResult.Invoke();
        this.InnerResult = innerFunctionResult;
    }
}

interface ISKFunction
{
    // Extension generic method to get from type <T>
    Task<StreamingFunctionResult<T>> InvokeStreamingAsync<T>(...);
}

static class KernelExtensions
{
    public static async Task<StreamingFunctionResult<T>> RunStreamingAsync<T>(this Kernel kernel, ISKFunction skFunction, ContextVariables? variables, CancellationToken cancellationToken)
    {
        ...
    }
}
```

## Pros

1. All benefits from Option 1 +
2. Having StreamingFunctionResults allow sk developer to know more details about the result before consuming the stream, like:
   - Any metadata provided by the underlying API,
   - SKContext
   - Function Name and Details
3. Experience using the Streaming is quite similar (need an extra await to get the result) to option 1
4. APIs behave similarly to the non-streaming API (returning a result representation to get the value)

## Cons

1. All cons from Option 1 +
2. Added complexity as the IAsyncEnumerable cannot be passed directly in the method result demanding a delegate approach to be adapted inside of the Results that implements the IAsyncEnumerator.
3. Added complexity where IDisposable is needed to be implemented in the Results to dispose the response object and the caller would need to handle the disposal of the result.
4. As soon the caller gets a `StreamingFunctionResult` a network connection will be kept open until the caller implementation consume it (Enumerate over the `IAsyncEnumerable`).

## Decision Outcome

Option 1 was chosen as the best option as small benefit of the Option 2 don't justify the complexity involved described in the Cons.

Was also decided that the Metadata related to a connector backend response can be added to the `StreamingContent.Metadata` property. This will allow the sk developer to get the metadata even without a `StreamingConnectorResult` or `StreamingFunctionResult`.
