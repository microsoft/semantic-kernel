// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Cclass with data related to function invocation.
/// </summary>
[Experimental("SKEXP0001")]
public class FunctionInvocationContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionFilterContext"/> class.
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
    /// Gets a dictionary of metadata associated with the operation.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; internal set; }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult? Result { get; internal set; }

    /// <summary>
    /// Gets the raw result of the function's invocation.
    /// </summary>
    internal object? ResultValue { get; private set; }

    /// <summary>
    /// Sets an object to use as the overridden new result for the function's invocation.
    /// </summary>
    /// <param name="value">The value to use as the new result of the function's invocation.</param>
    public void SetResultValue(object? value)
    {
        this.ResultValue = value;
    }
}
