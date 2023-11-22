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

## Considered Options

### Option 1 - Dedicated Streaming Interfaces

Using dedicated streaming interfaces that allow the sk developer to get the streaming data in a generic way, including string, byte array directly from the connector as well as allowing the Kernel and Functions implementations to be able to stream data of any type, not limited to text.

This approach also exposes dedicated interfaces in the kernel and functions to use streaming making it clear to the sk developer what is the type of data being returned in IAsyncEnumerable format.

`ITextCompletion` and `IChatCompletion` will have new APIs to get `byte[]` and `string` streaming data directly as well as the specialized `StreamingResultChunk` return.

The sk developer will be able to specify a generic type to the `Kernel.RunStreamingAsync<T>()` and `ISKFunction.StreamingInvokeAsync<T>` to get the streaming data. If the type is not specified, the Kernel and Functions will return the data as StreamingResultChunk.

If the type is not specified or if the string representation cannot be cast, an exception will be thrown.

If the type specified is `StreamingResultChunk`, `string` or `byte[]` no error will be thrown as the connectors will have interface methods that guarantee the data to be given in at least those types.

## User Experience Goal

```csharp
//(providing the type at as generic parameter)

// Getting a Raw Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingResultChunk as Streaming data from Kernel
await foreach(StreamingResultChunk update in kernel.RunStreamingAsync<StreamingResultChunk>(variables, function))
// OR
await foreach(StreamingResultChunk update in kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}
```

```csharp

// Depending on the underlying function model and connector used the streaming
// data will be of a specialization of StreamingResultChunk exposing useful
// properties including Type, the raw data in byte[] and string representation.
abstract class StreamingResultChunk
{
    public abstract string Type { get; }

    // In a scenario of multiple results, this represents zero-based index of the result in the streaming sequence
    public abstract int ResultIndex { get; }

    public abstract override string ToString();
    public abstract byte[] ToByteArray();

    public abstract object Contents { get; }
}

// Specialization example of a ChatMessageChunk
public class ChatMessageChunk : StreamingResultChunk
{
    public override string Type => "openai_chatmessage_chunk";
    public override string ToString() => Value.ToString(); // Value to be appended or the whole object?
    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(Value);

    public string Message { get; }
    public string Role { get; }

    public ChatMessageChunk(string message, string role, int resultIndex = 0)
    {
        Message = message;
        Role = role;
        ResultIndex = resultIndex;
    }
}

interface ITextCompletion + IChatCompletion
{
    IAsyncEnumerable<StreamingResultChunk> GetStreamingChunksAsync();
    // Guaranteed abstraction to be used by the ISKFunction.RunStreamingAsync()

    IAsyncEnumerable<T> GetStreamingChunksAsync<T>();
    // Throw exception if T is not supported
    // Initially connectors
}

interface IKernel
{
    // When the developer provides a T, the Kernel will try to get the streaming data as T
    IAsyncEnumerable<StreamingResultChunk> RunStreamingAsync(ContextVariables variables, ISKFunction function);

    // Extension generic method to get from type <T>
    IAsyncEnumerable<T> RunStreamingAsync<T>(ContextVariables variables, ISKFunction function);
}

public class StreamingFunctionResult : IAsyncEnumerable<StreamingResultChunk>
{

}

interface ISKFunction
{
    // When the developer provides a T, the Kernel will try to get the streaming data as T
    IAsyncEnumerable<StreamingResultChunk> InvokeStreamingAsync(SKContext context);

    // Extension generic method to get from type <T>
    IAsyncEnumerable<T> InvokeStreamingAsync<T>(SKContext context);
}
```

## Semantic Functions Behavior

When Semantic Functions are invoked using the Streaming API, they will attempt to use the Connectors streaming implementation. The connector will be responsible to provide the specialized type of `StreamingResultChunk` as well as to keep the API streaming working (streaming the single complete result) even when the backend don't support it.

## Native Functions Behavior

NativeFunctions will support StreamingResults automatically with a StreamingNativeResultUpdate wrapping the object returned in the iterator.

If NativeFunctions are already IAsyncEnumerable methods, the result will be automatically wrapped in the StreamingNativeResultUpdate keeping the streaming behavior and the overall abstraction consistent.

If NativeFunctions don't return IAsyncEnumerable, the result will be wrapped in a StreamingNativeResultUpdate and the result will be returned as a single result.

## Pros

1. All the User Experience Goal section options will be possible.
2. Kernel and Functions implementations will be able to stream data of any type, not limited to text
3. The sk developer will be able to provide the type it expects from the `GetStreamingResultAsync<T>` method.
4. The above will allow the sk developer to get the streaming data in a generic way, including `string`, `byte array`, or the `StreamingResultChunk` abstraction directly from the connector.

5. IChatCompletion, IKernel and ISKFunction

## Cons

1. If the sk developer wants to use the specialized type of `StreamingResultChunk` he will need to know what the connector is being used to use the correct **StreamingResultChunk extension method** or to provide directly type in `<T>`.
2. Connectors will have greater responsibility to provide the correct type of `StreamingResultChunk` for the connector being used and implementations for both byte[] and string streaming data.

### Option 2 - Dedicated Streaming Interfaces (Returning a Class)

This option includes all the suggestions from Option 1 with the only change being that the interfaces now instead of returning an `IAsyncEnumerable<T>` will return `StreamingFunctionResult<T>` which also implements `IAsyncEnumerable<T>`

Connectors will have a streaming connector class representation that will have any data related to the request as well as a breaking glass reference to the underlying connector object (response) if needed.

This abstraction is necessary to provide the extra connector information to the StreamingFunctionResult returned by KernelPromptFunctions.

## User Experience Goal

Option 2 Biggest benefit:

```csharp
// When the caller needs to know more about the streaming he can get the result reference before starting the streaming.
var streamingResult = await kernel.RunStreamingAsync(function);
// Do something with streamingResult properties

// Consuming the streamingResult:
await foreach(StreamingResultChunk chunk in await streamingResult)
```

Using the other operations will be quite similar (extra `await` to get the iteratable streaming reference) if the sk developer don't want to check for the result properties

````csharp
// Getting a Raw Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<byte[]>(function, variables))

// Getting a String as Streaming data from Kernel
await foreach(string update in await kernel.RunStreamingAsync<string>(function, variables))

// Getting a StreamingResultChunk as Streaming data from Kernel
await foreach(StreamingResultChunk update in await kernel.RunStreamingAsync<StreamingResultChunk>(variables, function))
// OR
await foreach(StreamingResultChunk update in await kernel.RunStreamingAsync(function, variables)) // defaults to Generic above)
{
    Console.WriteLine(update);
}
```

```csharp

public sealed class StreamingConnectorResult<T> : IAsyncEnumerable<T>
{
    private readonly IAsyncEnumerable<T> _streamingResultSource;

    /// <summary>
    /// Internal object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result.
    /// </summary>
    public object? InnerResult { get; private set; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConnectorAsyncEnumerable{T}"/> class.
    /// </summary>
    /// <param name="streamingReference"></param>
    /// <param name="innerConnectorResult"></param>
    public ConnectorAsyncEnumerable(Func<IAsyncEnumerable<T>> streamingReference, object? innerConnectorResult)
    {
        this._streamingResultSource = streamingReference.Invoke();
        this.InnerResult = innerConnectorResult;
    }
}

interface ITextCompletion + IChatCompletion
{
    Task<StreamingConnectorResult<StreamingResultChunk>> GetStreamingChunksAsync();
    // Guaranteed abstraction to be used by the ISKFunction.RunStreamingAsync()

    Task<StreamingConnectorResult<T>> GetStreamingChunksAsync<T>();
    // Throw exception if T is not supported
    // Initially connectors
}
```

StreamingFunctionResult is a class that can store information regarding the result before the stream is consumed as well as any underlying object (breaking glass) that the stream consumes.

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
    // When the developer provides a T, the Kernel will try to get the streaming data as T
    Task<StreamingFunctionResult<StreamingResultChunk>> InvokeStreamingAsync(...);

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


## Decision Outcome

Option 3
Try to use the Task<StreamingFunctionResult> interface with a dumb StreamingFunctionResult which wraps all the logic

## More Information
````
