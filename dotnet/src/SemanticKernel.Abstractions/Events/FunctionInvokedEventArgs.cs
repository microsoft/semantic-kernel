// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoked event.
/// </summary>
public class FunctionInvokedEventArgs : KernelCancelEventArgs
{
    /// <summary>
    /// Function result
    /// </summary>
    public FunctionResult Result { get; }

    /// <summary>
    /// Function result value
    /// </summary>
    internal object? ResultValue { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="arguments">Kernel function arguments</param>
    /// <param name="result">Function result</param>
    public FunctionInvokedEventArgs(KernelFunction function, KernelArguments arguments, FunctionResult result) : base(function, arguments)
    {
        this.Metadata = result.Metadata;
        this.Result = result;
        this.ResultValue = result.Value;
    }

    /// <summary>
    /// Set the function result value.
    /// </summary>
    /// <param name="value"></param>
    public void SetResultValue(object? value)
    {
        this.ResultValue = value;
    }
}
