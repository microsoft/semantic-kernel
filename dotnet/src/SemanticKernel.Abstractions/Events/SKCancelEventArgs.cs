// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;
#pragma warning disable CA1001 // Types that own disposable fields should be disposable

/// <summary>
/// Base arguments for cancellable events.
/// </summary>
public abstract class SKCancelEventArgs : SKEventArgs
{
    private CancellationTokenSource _cancelTokenSource = new();

    internal SKCancelEventArgs(FunctionView functionView, SKContext context) : base(functionView, context)
    {
    }

    /// <summary>
    /// Cancellation token to be used to cancel further execution.
    /// </summary>
    public CancellationToken CancelToken => this._cancelTokenSource.Token;

    /// <summary>
    /// Cancel all further execution.
    /// </summary>
    public void Cancel()
    {
        this._cancelTokenSource.Cancel();
    }

    /// <summary>
    /// Dispose resources.
    /// </summary>
    ~SKCancelEventArgs()
    {
        this._cancelTokenSource.Dispose();
    }
}
