// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public class FunctionInvokedEventArgs : CancelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="context">Context related to the event</param>
    public FunctionInvokedEventArgs(FunctionView functionView, SKContext context)
    {
        Verify.NotNull(context);
        this.FunctionView = functionView;
        this.SKContext = context;
    }

    /// <summary>
    /// Function view details.
    /// </summary>
    public FunctionView FunctionView { get; }

    /// <summary>
    /// SKContext after function was executed.
    /// </summary>
    public SKContext SKContext { get; }
}
