// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public sealed class FunctionInvokedEventArgs : EventArgs
{
    internal FunctionInvokedEventArgs(FunctionView functionView, SKContext context, string? prompt)
    {
        Verify.NotNull(context);
        this.FunctionView = functionView;
        this.SKContext = context;
        this.Prompt = prompt;
    }

    /// <summary>
    /// Function view details.
    /// </summary>
    public FunctionView FunctionView { get; }

    /// <summary>
    /// SKContext after function was executed.
    /// </summary>
    public SKContext SKContext { get; }

    /// <summary>
    /// Prompt that was rendered prior to the function execution.
    /// </summary>
    /// <remarks>
    /// May be null for native functions.
    /// </remarks>
    public string? Prompt { get; }
}
