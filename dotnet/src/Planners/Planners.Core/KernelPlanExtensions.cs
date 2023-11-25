// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Kernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Extension methods for running plans using a kernel
/// </summary>
public static class KernelPlanExtensions
{
    /*
    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="plan">The plan to invoke</param>
    /// <param name="input">Input to process</param>
    /// <returns>Result of the function</returns>
    public static Task<FunctionResult> InvokeAsync(
        this Kernel kernel,
        Plan plan,
        string? input = null)
    {
        return plan.InvokeAsync(kernel, input ?? string.Empty, new CancellationToken());
    }

    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="plan">The plan to invoke</param>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function</returns>
    public static Task<FunctionResult> InvokeAsync(
        this Kernel kernel,
        Plan plan,
        string input,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        var contextVariables = new ContextVariables();
        contextVariables.Update(input);

        return plan.InvokeAsync(kernel, contextVariables, null, cancellationToken);
    }
    */

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this Kernel kernel, Plan plan, CancellationToken cancellationToken = default)
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
    public static Task<Plan> StepAsync(this Kernel kernel, string input, Plan plan, CancellationToken cancellationToken = default)
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
    public static Task<Plan> StepAsync(this Kernel kernel, ContextVariables variables, Plan plan, CancellationToken cancellationToken = default)
    {
        return plan.RunNextStepAsync(kernel, variables, cancellationToken);
    }
}
