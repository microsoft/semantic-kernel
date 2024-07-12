// Copyright (c) Microsoft. All rights reserved.
using System.Threading;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public class ManualFunctionCallContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ManualFunctionCallContext"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    internal ManualFunctionCallContext(Kernel kernel, KernelFunction function, KernelArguments? arguments)
    {
        this.Kernel = kernel;
        this.Function = function;
        this.Arguments = arguments ?? [];
    }

    /// <summary>
    /// The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests.
    /// The default is <see cref="CancellationToken.None"/>.
    /// </summary>
    public CancellationToken CancellationToken { get; init; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult? Result { get; set; }
}
