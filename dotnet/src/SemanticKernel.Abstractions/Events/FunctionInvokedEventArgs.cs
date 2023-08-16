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
    internal FunctionInvokedEventArgs(FunctionView functionView, SKContext context)
    {
        Verify.NotNull(context);
        this.FunctionView = functionView;
        this.SKContext = context;
    }

    /// <summary>
    /// Function view details of the function that was executed.
    /// </summary>
    public FunctionView FunctionView { get; }

    /// <summary>
    /// Current SKContext changes after the function was executed.
    /// </summary>
    public SKContext SKContext { get; }
}
