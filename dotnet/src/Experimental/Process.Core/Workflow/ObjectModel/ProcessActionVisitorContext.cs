// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal delegate Task ProcessActionHandler(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel);

/// <summary>
/// Step context for the current step in a process.
/// </summary>
internal sealed class ProcessActionVisitorContext(ProcessStepBuilder step)
{
    /// <summary>
    /// The current step for the context.
    /// </summary>
    public ProcessStepBuilder Step { get; set; } = step;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <returns></returns>
    public ProcessStepEdgeBuilder Then() => this.Step.OnFunctionResult(KernelDelegateProcessStep.FunctionName);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="step"></param>
    /// <param name="condition"></param>
    /// <returns></returns>
    public ProcessStepBuilder Then(ProcessStepBuilder step, KernelProcessEdgeCondition? condition = null)
    {
        // IN: Target the given step when the previous step ends
        ProcessStepEdgeBuilder edge = this.Then();

        edge.Condition = condition;
        edge.SendEventTo(new ProcessFunctionTargetBuilder(step));

        return step;
    }
}
