// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel execution context
/// </summary>
public interface IKernelExecutionContext
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
    /// <param name="pipeline">Target functions to run in sequence</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
        ContextVariables variables,
        ISKFunction[] pipeline,
        CancellationToken cancellationToken = default);

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
