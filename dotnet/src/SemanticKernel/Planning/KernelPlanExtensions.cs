// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Extension methods for running plans using a kernel
/// </summary>
public static class KernelPlanExtensions
{
    /// <summary>
    /// Import a plan into the kernel
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to import</param>
    /// <returns>Function definition for the plan</returns>
    public static SkillDefinition.ISKFunction ImportPlan(this IKernel kernel, Plan plan)
    {
        return kernel.RegisterCustomFunction(plan);
    }

    /// <summary>
    /// Import a plan into the kernel
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="json">Json representation of the plan</param>
    /// <returns>Function definition for the plan</returns>
    public static SkillDefinition.ISKFunction ImportPlanFromJson(this IKernel kernel, string json)
    {
        return kernel.RegisterCustomFunction(Plan.FromJson(json, kernel.CreateNewContext()));
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, Plan plan, CancellationToken cancellationToken = default)
    {
        return kernel.StepAsync(plan.State, plan, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<Plan> StepAsync(this IKernel kernel, string input, Plan plan, CancellationToken cancellationToken = default)
    {
        return kernel.StepAsync(new ContextVariables(input), plan, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, ContextVariables variables, Plan plan, CancellationToken cancellationToken = default)
    {
        return plan.RunNextStepAsync(kernel, variables, cancellationToken);
    }
}
