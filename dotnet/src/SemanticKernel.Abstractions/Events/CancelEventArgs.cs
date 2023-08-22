// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;

namespace Microsoft.SemanticKernel.Events;
#pragma warning disable CA1001 // Types that own disposable fields should be disposable

/// <summary>
/// Base arguments for cancellable events.
/// </summary>
public abstract class CancelEventArgs : EventArgs
{
    private CancellationTokenSource _cancelTokenSource = new();

    public CancellationToken CancelToken => this._cancelTokenSource.Token;

    /// <summary>
    /// Cancel all further execution.
    /// </summary>
    public void Cancel()
    {
        this._cancelTokenSource.Cancel();
    }

    ~CancelEventArgs()
    {
        this._cancelTokenSource.Dispose();
    }
}
