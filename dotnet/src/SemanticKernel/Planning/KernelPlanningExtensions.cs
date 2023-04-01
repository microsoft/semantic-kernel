// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for running plans using a kernel
/// </summary>
public static class KernelPlanningExtensions
{
    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<IPlan> RunAsync(this IKernel kernel, IPlan plan)
    {
        return kernel.RunAsync(plan.State, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<IPlan> RunAsync(this IKernel kernel, IPlan plan, CancellationToken cancellationToken)
    {
        return kernel.RunAsync(plan.State, plan, cancellationToken);
    }

    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<IPlan> RunAsync(this IKernel kernel, string input, IPlan plan)
    {
        return kernel.RunAsync(input, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    public static Task<IPlan> RunAsync(this IKernel kernel, string input, IPlan plan, CancellationToken cancellationToken)
    {
        return kernel.RunAsync(new ContextVariables(input), plan, cancellationToken);
    }

    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<IPlan> RunAsync(this IKernel kernel, ContextVariables variables, IPlan plan)
    {
        return kernel.RunAsync(variables, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<IPlan> RunAsync(this IKernel kernel, ContextVariables variables, IPlan plan, CancellationToken cancellationToken)
    {
        return plan.RunNextStepAsync(kernel, variables, cancellationToken);
    }
}
