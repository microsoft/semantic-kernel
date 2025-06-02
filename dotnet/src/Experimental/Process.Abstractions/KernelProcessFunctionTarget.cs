// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the target for an edge in a Process
/// </summary>
[DataContract]
public record KernelProcessTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessTarget"/> class.
    /// </summary>
    /// <param name="type"></param>
    public KernelProcessTarget(ProcessTargetType type)
    {
        this.Type = type;
    }

    /// <summary>
    /// The type of target.
    /// </summary>
    public ProcessTargetType Type { get; init; } = ProcessTargetType.Invocation;
}

/// <summary>
/// Represents a state operations target for an edge in a Process
/// </summary>
[DataContract]
public record KernelProcessStateTarget : KernelProcessTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessStateTarget"/> class.
    /// </summary>
    public KernelProcessStateTarget(VariableUpdate variableUpdate) : base(ProcessTargetType.StateUpdate)
    {
        this.VariableUpdate = variableUpdate;
    }

    /// <summary>
    /// The associated <see cref="VariableUpdate"/>.
    /// </summary>
    [DataMember]
    public VariableUpdate VariableUpdate { get; init; }
}

/// <summary>
/// Represents a state operations target for an edge in a Process
/// </summary>
[DataContract]
public record KernelProcessEmitTarget : KernelProcessTarget
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEmitTarget"/> class.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="payload"></param>
    public KernelProcessEmitTarget(string eventName, Dictionary<string, string>? payload = null) : base(ProcessTargetType.StateUpdate)
    {
        Verify.NotNullOrWhiteSpace(eventName, nameof(eventName));
        this.EventName = eventName;
        this.Payload = payload;
    }

    /// <summary>
    /// The name or type of the event to be emitted.
    /// </summary>
    [DataMember]
    public string EventName { get; init; }

    /// <summary>
    /// /// The payload to be sent with the event.
    /// </summary>
    [DataMember]
    public Dictionary<string, string>? Payload { get; init; }
}

/// <summary>
/// Represents an agent invocation target for an edge in a Process
/// </summary>
[DataContract]
public record KernelProcessAgentInvokeTarget : KernelProcessTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessAgentInvokeTarget"/> class.
    /// </summary>
    /// <param name="stepId"></param>
    /// <param name="threadEval"></param>
    /// <param name="messagesInEval"></param>
    /// <param name="inputEvals"></param>
    public KernelProcessAgentInvokeTarget(string stepId, string? threadEval, List<string>? messagesInEval, Dictionary<string, string> inputEvals) : base(ProcessTargetType.Invocation)
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNull(inputEvals);

        this.StepId = stepId;
        this.ThreadEval = threadEval;
        this.MessagesInEval = messagesInEval;
        this.InputEvals = inputEvals;
    }

    /// <summary>
    /// The unique identifier of the Step being targeted.
    /// </summary>
    [DataMember]
    public string StepId { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the thread to run on.
    /// </summary>
    [DataMember]
    public string? ThreadEval { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the messages to send to the target.
    /// </summary>
    [DataMember]
    public List<string>? MessagesInEval { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the inputs to send to the target.
    /// </summary>
    [DataMember]
    public Dictionary<string, string> InputEvals { get; init; }
}

/// <summary>
/// A serializable representation of a specific parameter of a specific function of a specific Step.
/// </summary>
[DataContract]
public record KernelProcessFunctionTarget : KernelProcessTarget
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessFunctionTarget"/> class.
    /// </summary>
    public KernelProcessFunctionTarget(string stepId, string functionName, string? parameterName = null, string? targetEventId = null, Func<Dictionary<string, object?>, Dictionary<string, object?>>? inputMapping = null) : base(ProcessTargetType.KernelFunction)
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNullOrWhiteSpace(functionName);

        this.StepId = stepId;
        this.FunctionName = functionName;
        this.ParameterName = parameterName;
        this.TargetEventId = targetEventId;
        this.InputMapping = inputMapping;
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

    /// <summary>
    /// The mapping function to apply to the input data before passing it to the function.
    /// </summary>
    public Func<Dictionary<string, object?>, Dictionary<string, object?>>? InputMapping { get; init; }
}
