// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoking event.
/// </summary>
public class FunctionInvokingEventArgs : CancelEventArgs
{
    /// <summary>
    /// Indicates if the function execution should be skipped.
    /// </summary>
    public bool IsSkipRequested => this._skipRequested;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingEventArgs"/> class.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="context">Context related to the event</param>
    public FunctionInvokingEventArgs(FunctionView functionView, SKContext context)
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
    /// SKContext prior function execution.
    /// </summary>
    public SKContext SKContext { get; }

    /// <summary>
    /// Skip the current function invoking attempt.
    /// </summary>
    public void Skip()
    {
        this._skipRequested = true;
    }

    private bool _skipRequested;
}
