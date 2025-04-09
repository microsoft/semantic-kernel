// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process function target.
/// </summary>
public sealed record ProcessFunctionTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessFunctionTargetBuilder"/> class.
    /// </summary>
    /// <param name="step">The step to target.</param>
    /// <param name="functionName">The function to target.</param>
    /// <param name="parameterName">The parameter to target.</param>
    public ProcessFunctionTargetBuilder(ProcessStepBuilder step, string? functionName = null, string? parameterName = null)
    {
        Verify.NotNull(step, nameof(step));

        this.Step = step;

        // If the step is an EndStep, we don't need to resolve the function target.
        if (step is EndStep)
        {
            this.FunctionName = "END";
            this.ParameterName = null;
            return;
        }

        // Make sure the function target is valid.
        var target = step.ResolveFunctionTarget(functionName, parameterName);
        if (target == null)
        {
            throw new InvalidOperationException($"Failed to resolve function target for {step.GetType().Name}, {step.Name}: Function - {functionName ?? "any"} / Parameter - {parameterName ?? "any"}");
        }

        this.FunctionName = target.FunctionName!;
        this.ParameterName = target.ParameterName;
    }

    /// <summary>
    /// Builds the function target.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessFunctionTarget"/></returns>
    internal KernelProcessFunctionTarget Build()
    {
        Verify.NotNull(this.Step.Id);
        return new KernelProcessFunctionTarget(this.Step.Id, this.FunctionName, this.ParameterName, this.TargetEventId);
    }

    /// <summary>
    /// An instance of <see cref="ProcessStepBuilder"/> representing the target Step.
    /// </summary>
    public ProcessStepBuilder Step { get; init; }

    /// <summary>
    /// The name of the function to target.
    /// </summary>
    public string FunctionName { get; init; }

    /// <summary>
    /// The name of the parameter to target. This may be null if the function has no parameters.
    /// </summary>
    public string? ParameterName { get; init; }

    /// <summary>
    /// The unique identifier for the event to target. This may be null if the target is not a sub-process.
    /// </summary>
    public string? TargetEventId { get; init; }
}
