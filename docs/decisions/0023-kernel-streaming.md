---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-09-26
deciders: rbarreto,markwallace,sergey,dmytro
consulted:
informed:
---

# Streaming Capability for Kernel and Functions usage

## Context and Problem Statement

It is quite common in co-pilot implementations to have a streamlined output of messages from the LLM (large language models)M and currently that is not possible while using ISKFunctions.InvokeAsync or Kernel.RunAsync methods, which enforces users to work around the Kernel and Functions to use `ITextCompletion` and `IChatCompletion` services directly as the only interfaces that currently support streaming.

Currently streaming is a capability that not all providers do support and this as part of our design we try to ensure the services will have the proper abstractions to support streaming not only of text but be open to other types of data like images, audio, video, etc.

Needs to be clear for the sk developer when he is attempting to get streaming data.

## Decision Drivers

1. The sk developer should be able to get streaming data from the Kernel and Functions using Kernel.RunAsync or ISKFunctions.InvokeAsync methods

2. The sk developer should be able to get the data in a generic way, so the Kernel and Functions can be able to stream data of any type, not limited to text.

3. The sk developer when using streaming from a model that doesn't support streaming should still be able to use it with only one streaming update representing the whole data.

## User Experience Goal

```csharp
//(providing the type at as generic parameter)

// Getting a Raw Streaming data from Kernel
await foreach(string update in kernel.StreamingRunAsync<byte[]>(variables, function))

// Getting a String as Streaming data from Kernel
await foreach(string update in kernel.StreamingRunAsync<string>(variables, function))

// Getting a StreamingResultUpdate as Streaming data from Kernel
await foreach(StreamingResultUpdate update in kernel.StreamingRunAsync<StreamingResultUpdate>(variables, function))
// OR
await foreach(StreamingResultUpdate update in kernel.StreamingRunAsync(variables, function)) // defaults to Generic above)
{
    Console.WriteLine(update);
}
```

## Considered Options

### Option 1 - Dedicated Streaming Interfaces

Using dedicated streaming interfaces that allow the sk developer to get the streaming data in a generic way, including string, byte array directly from the connector as well as allowing the Kernel and Functions implementations to be able to stream data of any type, not limited to text.

This approach also exposes dedicated interfaces in the kernel and functions to use streaming making it clear to the sk developer what is the type of data being returned in IAsyncEnumerable format.

`ITextCompletion` and `IChatCompletion` will have new APIs to get `byte[]` and `string` streaming data directly as well as the specialized `StreamingResultUpdate` return.

The sk developer will be able to specify a generic type to the `Kernel.StreamingRunAsync<T>()` and `ISKFunction.StreamingInvokeAsync<T>` to get the streaming data. If the type is not specified, the Kernel and Functions will return the data as StreamingResultUpdate.

If the type isn't specified or if the string representation can't be cast, an exception will be thrown.

If the type specified is `StreamingResultUpdate`, `string` or `byte[]` no error will be thrown as the connectors will have interface methods that guarantee the data to be given in at least those types.

```csharp

// Depending on the underlying function model and connector used the streaming
// data will be of a specialization of StreamingResultUpdate exposing useful
// properties including Type, the raw data in byte[] and string representation.
abstract class StreamingResultUpdate
{
    public abstract string Type { get; }
    [JsonIgnore]
    public abstract string Value { get; }
    [JsonIgnore]
    public abstract byte[] RawValue { get; }

    // In a scenario of multiple results, this represents zero-based index of the result in the streaming sequence
    public abstract int ResultIndex { get; }
}

// Specialization example of a ChatMessageUpdate
public class ChatMessageUpdate : StreamingResultUpdate
{
    public override string Type => "ChatMessage";
    public override string Value => JsonSerialize(this);
    public override byte[] RawValue => Encoding.UTF8.GetBytes(Value);

    public string Message { get; }
    public string Role { get; }

    public ChatMessageUpdate(string message, string role, int resultIndex = 0)
    {
        Message = message;
        Role = role;
        ResultIndex = resultIndex;
    }
}

interface IChatCompletion
{
    IAsyncEnumerable<ChatMessageUpdate> GetStreamingResultAsync();
    IAsyncEnumerable<string> GetStringStreamingResultAsync();
    IAsyncEnumerable<byte[]> GetByteStreamingResultAsync();
}

interface ITextCompletion
{
    IAsyncEnumerable<TextMessageUpdate> GetStreamingResultAsync();
    IAsyncEnumerable<string> GetStringStreamingResultAsync();
    IAsyncEnumerable<byte[]> GetByteStreamingResultAsync();
}

interface IKernel
{
    // When the developer provides a T, the Kernel will try to get the streaming data as T
    IAsyncEnumerable<T> StreamingRunAsync<T>(ContextVariables variables, ISKFunction function);
}

interface ISKFunction
{
    // When the developer provides a T, the Kernel will try to get the streaming data as T
    IAsyncEnumerable<T> StreamingInvokeAsync<T>(SKContext context);
}
```

## Pros

1. All the User Experience Goal section options will be possible.
2. Kernel and Functions implementations will be able to stream data of any type, not limited to text
3. The sk developer will be able to provide the type it expects from the `GetStreamingResultAsync<T>` method.
4. The above will allow the sk developer to get the streaming data in a generic way, including `string`, `byte array`, or the `StreamingResultUpdate` abstraction directly from the connector.

5. IChatCompletion, IKernel and ISKFunction

## Cons

1. If the sk developer wants to use the specialized type of `StreamingResultUpdate` he will need to know what the connector is being used to use the correct **StreamingResultUpdate extension method** or to provide directly type in `<T>`.
2. Connectors will have greater responsibility to provide the correct type of `StreamingResultUpdate` for the connector being used and implementations for both byte[] and string streaming data.

## Decision Outcome

As for now, the only proposed solution is the #1.
