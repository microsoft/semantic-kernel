// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function runner extensions.
/// </summary>
public static class FunctionRunnerExtensions
{
    /// <summary>
    /// Execute a function using the resources loaded in the context.
    /// </summary>
    /// <param name="functionRunner">Target function runner</param>
    /// <param name="skFunction">Target function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this IFunctionRunner functionRunner,
        ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
    {
        return functionRunner.RunAsync(skFunction, variables, null, cancellationToken);
    }
}
