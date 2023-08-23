// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Semantic Function Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public sealed class SemanticFunctionInvokedEventArgs : FunctionInvokedEventArgs
{
    internal SemanticFunctionInvokedEventArgs(FunctionView functionView, SKContext context, string? renderedPrompt)
        : base(functionView, context)
    {
        this.RenderedPrompt = renderedPrompt;
    }

    /// <summary>
    /// Prompt rendered from template prior to the function execution.
    /// </summary>
    public string? RenderedPrompt { get; }
}
