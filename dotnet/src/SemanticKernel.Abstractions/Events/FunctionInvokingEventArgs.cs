// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoking event.
/// </summary>
public class FunctionInvokingEventArgs : KernelCancelEventArgs
{
    /// <summary>
    /// Indicates if the function execution should be skipped.
    /// </summary>
    public bool IsSkipRequested => this._skipRequested;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="arguments">Kernel function arguments</param>
    public FunctionInvokingEventArgs(KernelFunction function, KernelArguments arguments) : base(function, arguments)
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
