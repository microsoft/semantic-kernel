// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a <see cref="CancelKernelEventArgs"/> used in events just after a function is invoked.
/// </summary>
[Experimental("SKEXP0004")]
public sealed class FunctionInvokedEventArgs : CancelKernelEventArgs
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedEventArgs"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this event is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="result">The result of the function's invocation.</param>
    public FunctionInvokedEventArgs(KernelFunction function, KernelArguments arguments, FunctionResult result) :
        base(function, arguments, (result ?? throw new ArgumentNullException(nameof(result))).Metadata)
    {
        this.Result = result;
        this.ResultValue = result.Value;
    }

    /// <summary>Gets the result of the function's invocation.</summary>
    public FunctionResult Result { get; }

    /// <summary>Gets the raw result of the function's invocation.</summary>
    internal object? ResultValue { get; private set; }

    /// <summary>Sets an object to use as the overridden new result for the function's invocation.</summary>
    /// <param name="value">The value to use as the new result of the function's invocation.</param>
    public void SetResultValue(object? value)
    {
        this.ResultValue = value;
    }
}
