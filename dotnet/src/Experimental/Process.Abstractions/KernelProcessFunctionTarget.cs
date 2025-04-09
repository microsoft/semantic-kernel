// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a specific parameter of a specific function of a specific Step.
/// </summary>
[DataContract]
public record KernelProcessFunctionTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessFunctionTarget"/> class.
    /// </summary>
    public KernelProcessFunctionTarget(string stepId, string functionName, string? parameterName = null, string? targetEventId = null)
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNullOrWhiteSpace(functionName);

        this.StepId = stepId;
        this.FunctionName = functionName;
        this.ParameterName = parameterName;
        this.TargetEventId = targetEventId;
    }

    /// <summary>
    /// The unique identifier of the Step being targeted.
    /// </summary>
    [DataMember]
    public string StepId { get; init; }

    /// <summary>
    /// The name if the Kernel Function to target.
    /// </summary>
    [DataMember]
    public string FunctionName { get; init; }

    /// <summary>
    /// The name of the parameter to target. This may be null if the function has no parameters.
    /// </summary>
    [DataMember]
    public string? ParameterName { get; init; }

    /// <summary>
    /// The unique identifier for the event to target. This may be null if the target is not a sub-process.
    /// </summary>
    [DataMember]
    public string? TargetEventId { get; init; }
}
