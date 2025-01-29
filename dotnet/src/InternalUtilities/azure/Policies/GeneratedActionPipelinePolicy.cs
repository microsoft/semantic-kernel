// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Core.Pipeline;

/// <summary>
/// Generic action pipeline policy for processing messages.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class GenericActionPipelinePolicy : HttpPipelinePolicy
{
    private readonly Action<HttpMessage> _processMessageAction;

    internal GenericActionPipelinePolicy(Action<HttpMessage> processMessageAction)
    {
        this._processMessageAction = processMessageAction;
    }

    public override void Process(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        this._processMessageAction(message);
    }

    public override ValueTask ProcessAsync(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        this._processMessageAction(message);
        return new ValueTask(Task.CompletedTask); // .NET STD 2.0 compatibility
    }
}
