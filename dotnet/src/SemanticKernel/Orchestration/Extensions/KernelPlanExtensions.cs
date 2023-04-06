// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Extension methods for running plans using a kernel
/// </summary>
public static class KernelPlanExtensions
{
    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, Plan plan)
    {
        return kernel.StepAsync(plan.State, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, Plan plan, CancellationToken cancellationToken)
    {
        return kernel.StepAsync(plan.State, plan, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, string input, Plan plan)
    {
        return kernel.StepAsync(input, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    public static Task<Plan> StepAsync(this IKernel kernel, string input, Plan plan, CancellationToken cancellationToken)
    {
        return kernel.StepAsync(new ContextVariables(input), plan, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, ContextVariables variables, Plan plan)
    {
        return kernel.StepAsync(variables, plan, CancellationToken.None);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, ContextVariables variables, Plan plan, CancellationToken cancellationToken)
    {
        return plan.RunNextStepAsync(kernel, variables, cancellationToken);
    }
}
