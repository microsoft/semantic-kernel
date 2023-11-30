// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public class FunctionInvokedEventArgs : KernelCancelEventArgs
{
    /// <summary>
    /// Indicates if the function execution should repeat.
    /// </summary>
    public bool IsRepeatRequested => this._repeatRequested;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="arguments">Kernel function arguments</param>
    /// <param name="result">Function result</param>
    public FunctionInvokedEventArgs(KernelFunction function, KernelFunctionArguments arguments, FunctionResult result) : base(function, arguments)
    {
        this.Metadata = result.Metadata;
        this.Result = result;
    }

    /// <summary>Function result</summary>
    public FunctionResult Result { get; }

    /// <summary>
    /// Repeat the current function invocation.
    /// </summary>
    public void Repeat()
    {
        this._repeatRequested = true;
    }

    private bool _repeatRequested;
}
