// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

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
    IReadOnlyFunctionCollection Functions { get; }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="skFunction">Target function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        ISKFunction skFunction,
        ContextVariables variables,
        CancellationToken cancellationToken = default);
}
