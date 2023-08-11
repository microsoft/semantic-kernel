// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Context available to the post-execution handler.
/// </summary>
public sealed class PostExecutionContext
{
    internal PostExecutionContext(SKContext context)
    {
        Verify.NotNull(context);

        this.SKContext = context;
    }

    /// <summary>
    /// Current SKContext changes after the function was executed.
    /// </summary>
    public SKContext SKContext { get; }
}
