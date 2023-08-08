// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Context available to the pre-execution hook.
/// </summary>
public sealed class PreExecutionContext
{
    internal PreExecutionContext(SKContext context, string? prompt = null)
    {
        Verify.NotNull(context);

        this.SKContext = context;
        this.Prompt = prompt;
    }

    /// <summary>
    /// SKContext prior to sending to the LLM.
    /// </summary>
    public SKContext SKContext { get; }

    /// <summary>
    /// Prompt that was generated prior to sending to the LLM.
    /// </summary>
    /// <remarks>
    /// May be null for native functions.
    /// </remarks>
    public string? Prompt { get; }
}
