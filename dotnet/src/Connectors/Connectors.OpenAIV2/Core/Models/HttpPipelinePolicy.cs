// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal abstract class HttpPipelinePolicy : PipelinePolicy
{
    /// <summary>
    /// Invokes the next <see cref="HttpPipelinePolicy"/> in the <paramref name="pipeline"/>.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage"/> next policy would be applied to.</param>
    /// <param name="pipeline">The set of <see cref="HttpPipelinePolicy"/> to execute after next one.</param>
    /// <param name="currentIndex">Current index in the pipeline</param>
    /// <returns>The <see cref="ValueTask"/> representing the asynchronous operation.</returns>
    protected static ValueTask ProcessNextAsync(PipelineMessage message, ReadOnlyMemory<PipelinePolicy> pipeline, int currentIndex)
    {
        return pipeline.Span[0].ProcessAsync(message, pipeline.Slice(1).Span.ToArray(), currentIndex);
    }

    /// <summary>
    /// Invokes the next <see cref="HttpPipelinePolicy"/> in the <paramref name="pipeline"/>.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage"/> next policy would be applied to.</param>
    /// <param name="pipeline">The set of <see cref="HttpPipelinePolicy"/> to execute after next one.</param>
    /// <param name="currentIndex">Current index in the pipeline</param>
    protected static void ProcessNext(PipelineMessage message, ReadOnlyMemory<PipelinePolicy> pipeline, int currentIndex)
    {
        pipeline.Span[0].Process(message, pipeline.Slice(1).Span.ToArray(), currentIndex);
    }
}
