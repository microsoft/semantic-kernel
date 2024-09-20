// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A serializable representation of a specic parameter of a specific function of a specific Step.
/// </summary>
public record ProcessFunctionTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="ProcessFunctionTarget"/> class.
    /// </summary>
    /// <param name="stepId">The unique Id of the Step being targeted.</param>
    /// <param name="functionName">The name of Kernel Function being targeted.</param>
    /// <param name="parameterName">The name of the parameter being targeted.</param>
    public ProcessFunctionTarget(string stepId, string functionName, string? parameterName)
    {
        this.StepId = stepId;
        this.FunctionName = functionName;
        this.ParameterName = parameterName;
    }

    /// <summary>
    /// The unique identifier of the Step being targeted.
    /// </summary>
    public string StepId { get; init; }

    /// <summary>
    /// The name if the Kernel Function to target.
    /// </summary>
    public string FunctionName { get; init; }

    /// <summary>
    /// The name of the parameter to target.
    /// </summary>
    public string? ParameterName { get; init; }
}
