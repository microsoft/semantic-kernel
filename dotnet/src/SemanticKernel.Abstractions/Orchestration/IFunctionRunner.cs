// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function runner interface.
/// </summary>
public interface IFunctionRunner
{
    /// <summary>
    /// Execute a function using the resources loaded in the context.
    /// </summary>
    /// <param name="skFunction">Target function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    Task<FunctionResult> RunAsync(
        ISKFunction skFunction,
        ContextVariables variables,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Execute a function using the resources loaded in the context.
    /// </summary>
    /// <param name="pluginName">The name of the plugin containing the function to run</param>
    /// <param name="functionName">The name of the function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    Task<FunctionResult> RunAsync(
        string pluginName,
        string functionName,
        ContextVariables variables,
        CancellationToken cancellationToken = default);
}
