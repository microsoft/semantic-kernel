// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Semantic Function Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public sealed class SemanticFunctionInvokedEventArgs : FunctionInvokedEventArgs
{
    internal SemanticFunctionInvokedEventArgs(FunctionView functionView, SKContext context)
        : base(functionView, context)
    {
    }

    /// <summary>
    /// Prompt rendered from template after function invocation.
    /// </summary>
    public string? RenderedPrompt
    {
        get
        {
            this.SKContext.InternalVariables.TryGetValue(SemanticFunction.RenderedPromptKey, out string? renderedPrompt);
            return renderedPrompt;
        }
    }
}
