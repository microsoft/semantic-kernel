// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel execution context
/// </summary>
public interface IFunctionExecutor
{
    /// <summary>
    /// Execute a function using the resources loaded in the context.
    /// </summary>
    /// <param name="skFunction">Target function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="functions">Optional to override functions visible during the execution</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> ExecuteAsync(
        ISKFunction skFunction,
        ContextVariables variables,
        IReadOnlyFunctionCollection? functions = null,
        CancellationToken cancellationToken = default);
}
