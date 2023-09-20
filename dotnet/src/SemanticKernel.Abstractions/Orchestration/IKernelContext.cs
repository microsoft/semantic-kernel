// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.SkillDefinition;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel context reference
/// </summary>
public interface IKernelContext
{
    /// <summary>
    /// App logger
    /// </summary>
    ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Read only skills collection
    /// </summary>
    IReadOnlySkillCollection Skills { get; }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
        ContextVariables variables,
        CancellationToken cancellationToken = default,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Create a new instance of a context, linked to the kernel internal state.
    /// </summary>
    /// <param name="variables">Initializes the context with the provided variables</param>
    /// <param name="skills">Provide specific scoped skills. Defaults to all existing in the kernel</param>
    /// <returns>SK context</returns>
    SKContext CreateNewContext(
        ContextVariables? variables = null,
        IReadOnlySkillCollection? skills = null);
}

/// <summary>
/// Extension methods for <see cref="IKernelContext"/>
/// </summary>
public static class KernelContextExtensions
{
    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernelContext">Kernel context</param>
    /// <param name="input">Input</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(this IKernelContext kernelContext, string input, CancellationToken cancellationToken = default, params ISKFunction[] pipeline)
    {
        return kernelContext.RunAsync(new ContextVariables(input), cancellationToken, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernelContext">Kernel context</param>
    /// <param name="input">Input</param>
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <returns>Result of the function composition</returns>
    public static Task<SKContext> RunAsync(this IKernelContext kernelContext, string input, params ISKFunction[] pipeline)
    {
        return kernelContext.RunAsync(new ContextVariables(input), default, pipeline);
    }
}
