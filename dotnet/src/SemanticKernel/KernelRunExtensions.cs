// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extention methods to run a pipeline composed of synchronous and asynchronous functions.
/// </summary>
public static class KernelRunExtensions
{
    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        params ISKFunction[] pipeline)
        => RunAsync(kernel, new ContextVariables(), pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="input">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        string input,
        params ISKFunction[] pipeline)
        => RunAsync(kernel, new ContextVariables(input), pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="variables">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        ContextVariables variables,
        params ISKFunction[] pipeline)
        => RunAsync(kernel, variables, CancellationToken.None, pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
        => RunAsync(kernel, new ContextVariables(), cancellationToken, pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        string input,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
        => RunAsync(kernel, new ContextVariables(input), cancellationToken, pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        ContextVariables variables,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
        => kernel.RunAsync(new Plan(string.Empty, pipeline), variables, cancellationToken);
}
