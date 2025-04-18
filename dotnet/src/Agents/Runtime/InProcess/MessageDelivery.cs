// Copyright (c) Microsoft. All rights reserved.
// MessageDelivery.cs

namespace Microsoft.AgentRuntime.InProcess;

internal sealed class MessageDelivery(MessageEnvelope message, Func<MessageEnvelope, CancellationToken, ValueTask> servicer, IResultSink<object?> resultSink)
{
    public MessageEnvelope Message { get; } = message;
    public Func<MessageEnvelope, CancellationToken, ValueTask> Servicer { get; } = servicer;
    public IResultSink<object?> ResultSink { get; } = resultSink;

    public ValueTask InvokeAsync(CancellationToken cancellation)
    {
        return this.Servicer(this.Message, cancellation);
    }
}
