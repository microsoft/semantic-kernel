// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to function invocation.
/// </summary>
[Experimental("SKEXP0001")]
public class FunctionInvocationContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvocationContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    internal FunctionInvocationContext(KernelFunction function, KernelArguments arguments)
    {
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Function = function;
        this.Arguments = arguments;
    }

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
