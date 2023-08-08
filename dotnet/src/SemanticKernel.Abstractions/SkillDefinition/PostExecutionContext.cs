// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Context available to the post-execution hook.
/// </summary>
public sealed class PostExecutionContext
{
    internal PostExecutionContext(SKContext context)
    {
        Verify.NotNull(context);

        this.SKContext = context;
    }

    /// <summary>
    /// SKContext changes after LLM call and prior to returning the result to the caller.
    /// </summary>
    public SKContext SKContext { get; }
}
