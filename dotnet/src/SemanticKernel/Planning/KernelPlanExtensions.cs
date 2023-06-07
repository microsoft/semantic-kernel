// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
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
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="textCompletionService">Text completion service</param>
    /// <param name="settings">AI service settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, Plan plan, ITextCompletion? textCompletionService = null, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default)
    {
        return kernel.StepAsync(plan.State, plan, textCompletionService, settings, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="input">Input to use</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="textCompletionService">Text completion service</param>
    /// <param name="settings">AI service settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<Plan> StepAsync(this IKernel kernel, string input, Plan plan, ITextCompletion? textCompletionService = null, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default)
    {
        return kernel.StepAsync(new ContextVariables(input), plan, textCompletionService, settings, cancellationToken);
    }

    /// <summary>
    /// Run the next step in a plan asynchronously
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Input to process</param>
    /// <param name="plan">Plan to run</param>
    /// <param name="textCompletionService">Text completion service</param>
    /// <param name="settings">AI service settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the plan execution</returns>
    public static Task<Plan> StepAsync(this IKernel kernel, ContextVariables variables, Plan plan, ITextCompletion? textCompletionService = null, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default)
    {
        return plan.RunNextStepAsync(kernel, variables, textCompletionService, settings, cancellationToken);
    }
}
