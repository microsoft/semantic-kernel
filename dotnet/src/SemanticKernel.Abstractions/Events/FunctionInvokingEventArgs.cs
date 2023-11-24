// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoking event.
/// </summary>
public class FunctionInvokingEventArgs : SKCancelEventArgs
{
    /// <summary>
    /// Indicates if the function execution should be skipped.
    /// </summary>
    public bool IsSkipRequested => this._skipRequested;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingEventArgs"/> class.
    /// </summary>
    /// <param name="metadata">Function metadata</param>
    /// <param name="variables">Context variables relevant to the event</param>
    public FunctionInvokingEventArgs(SKFunctionMetadata metadata, ContextVariables variables) : base(metadata, variables)
    {
    }

    /// <summary>
    /// Skip the current function invoking attempt.
    /// </summary>
    public void Skip()
    {
        this._skipRequested = true;
    }

    private bool _skipRequested;
}
