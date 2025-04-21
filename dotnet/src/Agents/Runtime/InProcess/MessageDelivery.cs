// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess;

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
