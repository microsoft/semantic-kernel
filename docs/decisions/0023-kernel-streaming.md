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
    // Garanteed abstraction to be used by the ISKFunction.RunStreamingAsync()

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

## Decision Outcome

As for now, the only proposed solution is the #1.

## More Information

Think about generic for the interfaces...

StreamingFunctionResult ...

Look into Hugging Face Streaming APIs

Create a second option after talkin with Stephen.

Run by Matthew
StreamingAsync vs RunStreamingAsync vs RunStreamingAsync vs StreamAsync
First thing should be a verb

Add more examples of the API usage for streaming with chunks, for complex scenarios like multiple modals.

KDifferent impleme tations + differtnt consumers

I should be able to handle stuff that i don't know.
