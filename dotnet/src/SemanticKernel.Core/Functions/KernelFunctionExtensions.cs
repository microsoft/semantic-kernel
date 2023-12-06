// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Sponsor class for extension methods for <see cref="KernelFunction"/>.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Invokes the<see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernelFunction">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The provided generic typed result value of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    public static async Task<TResult?> InvokeAsync<TResult>(
        this KernelFunction kernelFunction,
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
        => (await kernelFunction.InvokeAsync(kernel, arguments, cancellationToken).ConfigureAwait(false)).GetValue<TResult>();
}
