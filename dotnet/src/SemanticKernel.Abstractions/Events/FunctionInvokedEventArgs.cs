// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public class FunctionInvokedEventArgs : SKCancelEventArgs
{
    private Dictionary<string, object>? _metadata;

    /// <summary>
    /// Indicates if the function execution should repeat.
    /// </summary>
    public bool IsRepeatRequested => this._repeatRequested;

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata => this._metadata ??= new();

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="result">Function result</param>
    public FunctionInvokedEventArgs(FunctionView functionView, FunctionResult result) : base(functionView, result.Context)
    {
        this._metadata = result._metadata;
    }

    /// <summary>
    /// Repeat the current function invocation.
    /// </summary>
    public void Repeat()
    {
        this._repeatRequested = true;
    }

    private bool _repeatRequested;
}
