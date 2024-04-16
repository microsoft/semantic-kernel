// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to function calling invocation.
/// </summary>
[Experimental("SKEXP0001")]
public class FunctionCallInvocationContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCallInvocationContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="result">The result of the function's invocation.</param>
    public FunctionCallInvocationContext(
        KernelFunction function,
        FunctionResult result)
    {
        Verify.NotNull(function);
        Verify.NotNull(result);

        this.Function = function;
        this.Result = result;
    }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// Request iteration number of function calling loop. Starts from 0.
    /// </summary>
    public int RequestIteration { get; init; }

    /// <summary>
    /// Function call iteration number. Starts from 0.
    /// This property indicates iteration of function call as part of the same request.
    /// It's useful when single request returns multiple function calls.
    /// </summary>
    public int FunctionCallIteration { get; init; }

    /// <summary>
    /// Total number of function calls to perform within single iteration request.
    /// </summary>
    public int FunctionCallCount { get; init; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; set; }

    /// <summary>
    /// Gets or sets function call iteration action.
    /// </summary>
    public FunctionCallAction Action { get; set; }
}
