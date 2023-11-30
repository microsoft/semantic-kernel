// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Class that holds extension methods for objects implementing KernelFunction.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="kernel">Kernel</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="executionSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this KernelFunction function,
        Kernel kernel,
        string input,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        KernelArguments? arguments = executionSettings is not null ? new(executionSettings) : null;
        if (!string.IsNullOrEmpty(input))
        {
            (arguments ??= new()).Add(KernelArguments.InputParameterName, input);
        }

        return function.InvokeAsync(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="function">Target function</param>
    /// <param name="kernel">The kernel</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="executionSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public static IAsyncEnumerable<T> InvokeStreamingAsync<T>(this KernelFunction function,
        Kernel kernel,
        string input,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        KernelArguments? arguments = executionSettings is not null ? new(executionSettings) : null;
        if (!string.IsNullOrEmpty(input))
        {
            (arguments ??= new()).Add(KernelArguments.InputParameterName, input);
        }

        return function.InvokeStreamingAsync<T>(kernel, arguments, cancellationToken);
    }
}
