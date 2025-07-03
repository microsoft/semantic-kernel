// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining targets to listen for in a process.
/// </summary>
public sealed partial class ListenForTargetBuilder : ProcessStepEdgeBuilder
{
    private readonly ProcessBuilder _processBuilder;
    private readonly List<MessageSourceBuilder> _messageSources = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForTargetBuilder"/> class.
    /// </summary>
    /// <param name="messageSources">The list of message sources.</param>
    /// <param name="processBuilder">The process builder.</param>
    /// <param name="edgeGroup">The group ID for the message sources.</param>
    public ListenForTargetBuilder(List<MessageSourceBuilder> messageSources, ProcessBuilder processBuilder, KernelProcessEdgeGroupBuilder? edgeGroup = null) : base(processBuilder, "Aggregate", "Aggregate", edgeGroupBuilder: edgeGroup)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        this._messageSources = messageSources;
        this._processBuilder = processBuilder;
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo(ProcessStepTargetBuilder target)
    {
        if (!target.Step.InputParametersTypeData.TryGetValue(target.FunctionName, out var targetFunction))
        {
            throw new InvalidOperationException($"Function '{target.FunctionName}' not found in target step {target.Step.StepId}");
        }

        var incomingEventTypes = this._messageSources.Select(m => m.Source.OutputStepEvents[m.MessageType].EventTypeData?.DataType).ToList();

        //foreach (var inputParameter in targetFunction.Values)
        //{
        //    if (!incomingEventTypes.Contains(inputParameter.DataType))
        //    {
        //        throw new InvalidOperationException($"Input parameter '{inputParameter.DataType?.Name}' of type '{inputParameter.DataType.Name}' does not match any of the incoming event types: {string.Join(", ", incomingEventTypes)}");
        //    }
        //}

        // TODO: For now strict parameter validation cannot be done, but type check can be done to make sure parameters are type compatible.
        // Specific mapping of parameters from inputMapping needs restructure to be validated at the builder stage.

        return this.SendEventTo_Internal(target);
    }

    /// <summary>
    /// Signals that the specified state variable should be updated in the process state.
    /// </summary>
    /// <param name="path"></param>
    /// <param name="operation"></param>
    /// <param name="value"></param>
    /// <returns></returns>
    internal ListenForTargetBuilder UpdateProcessState(string path, StateUpdateOperations operation, object? value)
    {
        Verify.NotNullOrWhiteSpace(path);

        if (!path.StartsWith(ProcessConstants.Declarative.VariablePrefix, StringComparison.OrdinalIgnoreCase))
        {
            path = $"{ProcessConstants.Declarative.VariablePrefix}.{path}";
        }

        // TODO: Should metadata go into the target now?
        this.VariableUpdate = new VariableUpdate { Path = path, Operation = operation, Value = value };
        this.SendEventTo_Internal(new ProcessStateTargetBuilder(this.VariableUpdate));

        return new ListenForTargetBuilder(this._messageSources, this._processBuilder, this.EdgeGroupBuilder);
    }

    /// <summary>
    /// Signals that the specified event should be emitted.
    /// </summary>
    /// <param name="eventName"></param>
    /// <param name="payload"></param>
    /// <returns></returns>
    internal ListenForTargetBuilder EmitEvent(string eventName, Dictionary<string, string>? payload = null)
    {
        Verify.NotNullOrWhiteSpace(eventName, nameof(eventName));
        this.SendEventTo_Internal(new ProcessEmitTargetBuilder(eventName, payload));
        return new ListenForTargetBuilder(this._messageSources, this._processBuilder, this.EdgeGroupBuilder);
    }

    /// <summary>
    /// Sends the event to the specified target.
    /// </summary>
    /// <param name="target">The target to send the event to.</param>
    /// <returns>A new instance of <see cref="ListenForTargetBuilder"/>.</returns>
    internal override ProcessStepEdgeBuilder SendEventTo_Internal(ProcessTargetBuilder target)
    {
        foreach (var messageSource in this._messageSources)
        {
            if (messageSource.Source == null)
            {
                throw new InvalidOperationException("Source step cannot be null.");
            }

            // Link all the source steps to the event listener
            ProcessStepEdgeBuilder? onEventBuilder = null;

            if (messageSource.Source is ProcessBuilder processSource && !processSource.HasParentProcess)
            {
                // process has no parent, it is root process an only output event from root is external input events
                onEventBuilder = processSource.OnInputEvent(messageSource.MessageType);
            }
            else
            {
                // if it is a process and has parent process, process is seen as step by other steps.
                // if it is a step it seen as step by other steps
                onEventBuilder = messageSource.Source.OnEvent(messageSource.MessageType);
            }

            onEventBuilder.EdgeGroupBuilder = this.EdgeGroupBuilder;

            if (messageSource.Condition != null)
            {
                onEventBuilder.Condition = messageSource.Condition;
            }
            onEventBuilder.SendEventTo(target);
        }

        return new ListenForTargetBuilder(this._messageSources, this._processBuilder, edgeGroup: this.EdgeGroupBuilder);
    }

    /// <summary>
    /// Signals that the process should be stopped.
    /// </summary>
    public override void StopProcess()
    {
        var target = new ProcessFunctionTargetBuilder(EndStep.Instance);

        foreach (var messageSource in this._messageSources)
        {
            if (messageSource.Source == null)
            {
                throw new InvalidOperationException("Source step cannot be null.");
            }

            // Link all the source steps to the event listener
            var onEventBuilder = messageSource.Source.OnEvent(messageSource.MessageType);
            onEventBuilder.EdgeGroupBuilder = this.EdgeGroupBuilder;
            onEventBuilder.SendEventTo(target);
        }
    }
}
