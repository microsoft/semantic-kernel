// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to function after invocation.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionInvokedContext : FunctionFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedContext"/> class.
    /// </summary>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="result">The result of the function's invocation.</param>
    public FunctionInvokedContext(KernelArguments arguments, FunctionResult result)
        : base(result.Function, arguments, (result ?? throw new ArgumentNullException(nameof(result))).Metadata)
    {
        this.Result = result;
        this.ResultValue = result.Value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionInvokedContext"/> class.
    /// </summary>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="result">The result of the function's invocation.</param>
    /// <param name="exception">The exception that occurred during function invocation.</param>
    public FunctionInvokedContext(KernelArguments arguments, FunctionResult result, Exception exception)
        : this(arguments, result)
    {
        this.Exception = exception;
    }

    /// <summary>
    /// Gets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; }

    /// <summary>
    /// Gets the exception that occurred during function invocation.
    /// If it's <see langword="null" />, it means that function invocation was completed successfully.
    /// </summary>
    public Exception? Exception { get; private set; }

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

    /// <summary>
    /// Cancels exception throwing after function invocation.
    /// </summary>
    public void CancelException()
    {
        this.Exception = null;
    }
}
