// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using System.Threading;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function executor interface extensions
/// </summary>
public static class FunctionExecutorExtension
{
    /// <summary>
    /// Execute a function using the resources loaded in the context.
    /// </summary>
    /// <param name="functionExecutor"></param>
    /// <param name="skFunction">Target function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> ExecuteAsync(this IFunctionExecutor functionExecutor,
        ISKFunction skFunction,
        ContextVariables variables,
        CancellationToken cancellationToken = default)
    {
        return functionExecutor.ExecuteAsync(skFunction, variables, null, cancellationToken);
    }
}
