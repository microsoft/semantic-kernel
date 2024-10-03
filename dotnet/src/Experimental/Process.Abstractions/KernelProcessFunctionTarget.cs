// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a specific parameter of a specific function of a specific Step.
/// </summary>
public record KernelProcessFunctionTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessFunctionTarget"/> class.
    /// </summary>
    public KernelProcessFunctionTarget(string stepId, string functionName, string? parameterName = null)
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNullOrWhiteSpace(functionName);

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
    /// The name of the parameter to target. This may be null if the function has no parameters.
    /// </summary>
    public string? ParameterName { get; init; }
}
