// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Kernel function extensions class.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="function">Target function</param>
    /// <param name="kernel">The kernel</param>
    /// <param name="arguments">The function arguments</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public static IAsyncEnumerable<StreamingContent> InvokeStreamingAsync(
        this KernelFunction function,
        Kernel kernel,
        KernelFunctionArguments arguments,
        CancellationToken cancellationToken = default)
    {
        return function.InvokeStreamingAsync<StreamingContent>(kernel, arguments, cancellationToken);
    }
}
