// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Policies;
/// <summary>
/// Represents a custom HTTP pipeline no retry policy.
/// </summary>
public class NoRetryPolicy : HttpPipelinePolicy
{
    /// <inheritdoc/>
    public override void Process(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        ProcessNext(message, pipeline);
    }

    /// <inheritdoc/>
    public override async ValueTask ProcessAsync(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        await ProcessNextAsync(message, pipeline).ConfigureAwait(false);
    }
}
