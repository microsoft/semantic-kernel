// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Policies;
/// <summary>
/// Represents a custom HTTP pipeline no retry policy.
/// NOTE: Replace the use of this class with the new RetryPolicy(maxRetries: 0) once a new version of the Azure.AI.OpenAI nuget package, which includes a public version of the RetryPolicy class, is released.
/// </summary>
internal sealed class NoRetryPolicy : HttpPipelinePolicy
{
    /// <inheritdoc/>
    public override void Process(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        ProcessNext(message, pipeline);
    }

    /// <inheritdoc/>
    public override ValueTask ProcessAsync(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        return ProcessNextAsync(message, pipeline);
    }
}
