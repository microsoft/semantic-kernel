// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;
#pragma warning disable CA1001 // Types that own disposable fields should be disposable

/// <summary>
/// Base arguments for cancellable events.
/// </summary>
public abstract class KernelCancelEventArgs : KernelEventArgs
{
    private readonly CancellationTokenSource _cancelTokenSource = new();

    internal KernelCancelEventArgs(KernelFunction function, ContextVariables variables) : base(function, variables)
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
}
