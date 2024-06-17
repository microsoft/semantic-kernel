// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to function HTTP request message creation.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionRequestMessageContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionRequestMessageContext"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    public FunctionRequestMessageContext(
        Kernel kernel,
        KernelFunction function)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(function);

        this.Kernel = kernel;
        this.Function = function;
    }
    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }
}
