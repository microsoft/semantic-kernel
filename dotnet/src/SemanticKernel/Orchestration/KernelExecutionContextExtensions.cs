// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Extension methods for <see cref="IKernelExecutionContext"/>
/// </summary>
public static class KernelExecutionContextExtensions
{
    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernelContext">Kernel context</param>
    /// <param name="input">Input</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(this IKernelExecutionContext kernelContext, string input, ISKFunction[] pipeline, CancellationToken cancellationToken = default)
    {
        return kernelContext.RunAsync(new ContextVariables(input), pipeline, cancellationToken);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernelContext">Kernel context</param>
    /// <param name="input">Input</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(this IKernelExecutionContext kernelContext, string input, ISKFunction pipeline)
    {
        return kernelContext.RunAsync(new ContextVariables(input), new[] { pipeline }, default);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernelContext">Kernel context</param>
    /// <param name="variables">Context variables</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(this IKernelExecutionContext kernelContext, ContextVariables variables, ISKFunction pipeline, CancellationToken cancellationToken = default)
    {
        return kernelContext.RunAsync(variables, new[] { pipeline }, cancellationToken);
    }
}
