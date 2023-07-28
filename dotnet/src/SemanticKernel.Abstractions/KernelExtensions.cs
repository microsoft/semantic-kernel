// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension menthods for the <see cref="IKernel"/> interface.
/// </summary>
public static class KernelExtensions
{
    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="function"></param>
    /// <param name="input"></param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function</returns>
    /// <returns></returns>
    public static Task<SKContext> RunAsync(
        this IKernel kernel,
        ISKFunction function,
        string input,
        CancellationToken cancellationToken = default)
        => kernel.RunAsync(function, new ContextVariables(input), cancellationToken);
}
