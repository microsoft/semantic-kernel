// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process target.
/// </summary>
public abstract record ProcessTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessTargetBuilder"/> class.
    /// </summary>
    /// <param name="type"></param>
    internal ProcessTargetBuilder(ProcessTargetType type)
    {
        this.Type = type;
    }

    /// <summary>
    /// The type of target.
    /// </summary>
    public ProcessTargetType Type { get; init; }

    /// <summary>
    /// Builds the target.
    /// </summary>
    /// <param name="processBuilder"></param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    internal abstract KernelProcessTarget Build(ProcessBuilder? processBuilder = null);
}

/// <summary>
/// Provides functionality for incrementally defining a process invocation target.
/// </summary>
public record ProcessStateTargetBuilder : ProcessTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStateTargetBuilder"/> class.
    /// </summary>
    /// <param name="variableUpdate"></param>
    public ProcessStateTargetBuilder(VariableUpdate variableUpdate) : base(ProcessTargetType.StateUpdate)
    {
        Verify.NotNull(variableUpdate, nameof(variableUpdate));
        this.VariableUpdate = variableUpdate;
    }

    /// <summary>
    /// The variable update to be performed when the target is reached.
    /// </summary>
    public VariableUpdate VariableUpdate { get; init; }

    internal override KernelProcessTarget Build(ProcessBuilder? processBuilder = null)
    {
        return new KernelProcessStateTarget(this.VariableUpdate);
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process invocation target.
/// </summary>
public record ProcessEmitTargetBuilder : ProcessTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessEmitTargetBuilder"/> class.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="payload"></param>
    public ProcessEmitTargetBuilder(string eventName, Dictionary<string, string>? payload = null) : base(ProcessTargetType.StateUpdate)
    {
        Verify.NotNullOrWhiteSpace(eventName, nameof(eventName));
        this.EventName = eventName;
        this.Payload = payload;
    }

    /// <summary>
    /// The name or type of the event to be emitted.
    /// </summary>
    public string EventName { get; init; }

    /// <summary>
    /// /// The payload to be sent with the event.
    /// </summary>
    public Dictionary<string, string>? Payload { get; init; }

    internal override KernelProcessTarget Build(ProcessBuilder? processBuilder = null)
    {
        return new KernelProcessEmitTarget(this.EventName, this.Payload);
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process agent invocation target.
/// </summary>
public record ProcessAgentInvokeTargetBuilder : ProcessTargetBuilder
{
    /// <summary>
    /// Creates an instance of the <see cref="KernelProcessAgentInvokeTarget"/> class.
    /// </summary>
    /// <param name="step"></param>
    /// <param name="threadEval"></param>
    /// <param name="messagesInEval"></param>
    /// <param name="inputEvals"></param>
    public ProcessAgentInvokeTargetBuilder(ProcessStepBuilder step, string? threadEval, List<string>? messagesInEval, Dictionary<string, string> inputEvals) : base(ProcessTargetType.Invocation)
    {
        Verify.NotNull(step);
        Verify.NotNull(inputEvals);

        this.Step = step;
        this.ThreadEval = threadEval;
        this.MessagesInEval = messagesInEval;
        this.InputEvals = inputEvals;
    }

    /// <summary>
    /// The unique identifier of the Step being targeted.
    /// </summary>
    public ProcessStepBuilder Step { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the thread to run on.
    /// </summary>
    public string? ThreadEval { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the messages to send to the target.
    /// </summary>
    public List<string>? MessagesInEval { get; init; }

    /// <summary>
    /// An evaluation string that will be evaluated to determine the inputs to send to the target.
    /// </summary>
    public Dictionary<string, string> InputEvals { get; init; }

    internal override KernelProcessTarget Build(ProcessBuilder? processBuilder = null)
    {
        return new KernelProcessAgentInvokeTarget(this.Step.Id, this.ThreadEval, this.MessagesInEval, this.InputEvals);
    }
}

/// <summary>
/// Provides functionality for incrementally defining a process function target.
/// </summary>
public record ProcessFunctionTargetBuilder : ProcessTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessFunctionTargetBuilder"/> class.
    /// </summary>
    /// <param name="step">The step to target.</param>
    /// <param name="functionName">The function to target.</param>
    /// <param name="parameterName">The parameter to target.</param>
    public ProcessFunctionTargetBuilder(ProcessStepBuilder step, string? functionName = null, string? parameterName = null) : base(ProcessTargetType.KernelFunction)
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
    internal override KernelProcessTarget Build(ProcessBuilder? processBuilder = null)
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

/// <summary>
/// Provides functionality for incrementally defining a process step target.
/// </summary>
public sealed record ProcessStepTargetBuilder : ProcessFunctionTargetBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepTargetBuilder"/> class.
    /// </summary>
    /// <param name="stepBuilder"></param>
    /// <param name="inputMapping"></param>
    public ProcessStepTargetBuilder(ProcessStepBuilder stepBuilder, Func<Dictionary<string, object?>, Dictionary<string, object?>>? inputMapping = null) : base(stepBuilder)
    {
        this.InputMapping = inputMapping ?? new Func<Dictionary<string, object?>, Dictionary<string, object?>>((input) => input);
    }

    /// <summary>
    /// An instance of <see cref="ProcessStepBuilder"/> representing the target Step.
    /// </summary>
    public Func<Dictionary<string, object?>, Dictionary<string, object?>> InputMapping { get; init; }
}
