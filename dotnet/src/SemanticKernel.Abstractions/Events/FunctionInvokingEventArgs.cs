// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Events;

/// <summary>
/// Event arguments available to the Kernel.FunctionInvoking event.
/// </summary>
public class FunctionInvokingEventArgs : KernelCancelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokingEventArgs"/> class.
    /// </summary>
    /// <param name="function">Kernel function</param>
    /// <param name="arguments">Kernel function arguments</param>
    public FunctionInvokingEventArgs(KernelFunction function, KernelArguments arguments) : base(function, arguments)
    {
    }
}
