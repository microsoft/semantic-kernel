// Copyright (c) Microsoft. All rights reserved.

/* Phase 03
Adapted from OpenAI SDK original policy with warning updates.

Original file: https://github.com/openai/openai-dotnet/blob/0b97311f58dfb28bd883d990f68d548da040a807/src/Utility/GenericActionPipelinePolicy.cs#L8
*/

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;

/// <summary>
/// Generic action pipeline policy for processing messages.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class GenericActionPipelinePolicy : PipelinePolicy
{
    private readonly Action<PipelineMessage> _processMessageAction;

    internal GenericActionPipelinePolicy(Action<PipelineMessage> processMessageAction)
    {
        this._processMessageAction = processMessageAction;
    }

    public override void Process(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this._processMessageAction(message);
        if (currentIndex < pipeline.Count - 1)
        {
            pipeline[currentIndex + 1].Process(message, pipeline, currentIndex + 1);
        }
    }

    public override async ValueTask ProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this._processMessageAction(message);
        if (currentIndex < pipeline.Count - 1)
        {
            await pipeline[currentIndex + 1].ProcessAsync(message, pipeline, currentIndex + 1).ConfigureAwait(false);
        }
    }
}
