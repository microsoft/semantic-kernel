// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public class FunctionInvokedEventArgs : SKCancelEventArgs
{
    /// <summary>
    /// Indicates if the function execution should repeat.
    /// </summary>
    public bool IsRepeatRequested => this._repeatRequested;

    /// <summary>
    /// Model results after function execution.
    /// </summary>
    public IReadOnlyCollection<ModelResult> ModelResults { get; private set; } = Array.Empty<ModelResult>();

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="result">Function result</param>
    public FunctionInvokedEventArgs(FunctionView functionView, FunctionResult result) : base(functionView, result.Context)
    {
        this.ModelResults = result.ModelResults;
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
