// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public class ProcessStepEdgeBuilder
{
    internal ProcessTargetBuilder? Target { get; set; }

    /// <summary>
    /// The event data that the edge fires on.
    /// </summary>
    internal ProcessEventData EventData { get; }

    /// <summary>
    /// The source step of the edge.
    /// </summary>
    internal ProcessStepBuilder Source { get; }

    /// <summary>
    /// The EdgeGroupBuilder for the edge
    /// </summary>
    internal KernelProcessEdgeGroupBuilder? EdgeGroupBuilder { get; set; }

    /// <summary>
    /// The condition that must be met for the edge to fire.
    /// </summary>
    internal KernelProcessEdgeCondition? Condition { get; set; }

    /// <summary>
    /// An optional variable update to be performed when the edge fires.
    /// </summary>
    internal VariableUpdate? VariableUpdate { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    /// <param name="eventName"></param>
    /// <param name="edgeGroupBuilder">The group Id for the edge.</param>
    /// <param name="condition">The condition that must be met for the edge to fire.</param>
    internal ProcessStepEdgeBuilder(ProcessStepBuilder source, string eventId, string eventName, KernelProcessEdgeGroupBuilder? edgeGroupBuilder = null, KernelProcessEdgeCondition? condition = null)
    {
        Verify.NotNull(source, nameof(source));
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        this.Source = source;
        this.EventData = new() { EventId = eventId, EventName = eventName };
        this.EdgeGroupBuilder = edgeGroupBuilder;
        this.Condition = condition;
    }

    /// <summary>
    /// Builds the edge.
    /// </summary>
    internal KernelProcessEdge Build(ProcessBuilder? processBuilder = null)
    {
        Verify.NotNull(this.Source?.StepId);

        if (this.Target is null || this.Source?.StepId is null)
        {
            throw new InvalidOperationException("A target and Source must be specified before building the edge.");
        }

        if (this.Target is ProcessFunctionTargetBuilder functionTargetBuilder)
        {
            if (this.EdgeGroupBuilder is not null && this.Target is ProcessStepTargetBuilder stepTargetBuilder)
            {
                var messageSources = this.EdgeGroupBuilder.MessageSources.Select(e => new KernelProcessMessageSource(e.MessageType, e.Source.StepId)).ToList();
                var edgeGroup = new KernelProcessEdgeGroup(this.EdgeGroupBuilder.GroupId, messageSources, stepTargetBuilder.InputMapping);
                functionTargetBuilder.Step.RegisterGroupInputMapping(edgeGroup);
            }
        }

        return new KernelProcessEdge(this.Source.StepId, this.Target.Build(processBuilder), groupId: this.EdgeGroupBuilder?.GroupId, this.Condition, this.VariableUpdate);
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo(ProcessTargetBuilder target)
    {
        return this.SendEventTo_Internal(target);
    }

    /// <summary>
    /// Sets the condition for the edge.
    /// </summary>
    /// <param name="condition"></param>
    /// <returns></returns>
    public ProcessStepEdgeBuilder OnCondition(KernelProcessEdgeCondition condition)
    {
        Verify.NotNull(condition, nameof(condition));
        this.Condition = condition;
        return this;
    }

    /// <summary>
    /// Internally overridable implementation: Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    /// <exception cref="InvalidOperationException"></exception>
    /// <exception cref="ArgumentException"></exception>
    internal virtual ProcessStepEdgeBuilder SendEventTo_Internal(ProcessTargetBuilder target)
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        if (target is ProcessFunctionTargetBuilder functionTargetBuilder)
        {
            if (functionTargetBuilder.Step is ProcessMapBuilder && this.Source is ProcessMapBuilder)
            {
                throw new ArgumentException($"{nameof(ProcessMapBuilder)} may not target another {nameof(ProcessMapBuilder)}.", nameof(target));
            }
        }

        this.Target = target;
        this.Source.LinkTo(this.EventData.EventId, this);

        return new ProcessStepEdgeBuilder(this.Source, this.EventData.EventId, this.EventData.EventName, this.EdgeGroupBuilder, this.Condition);
    }

    /// <summary>
    /// Emit the SK step event as an external event with specific topic name
    /// </summary>
    /// <returns></returns>
    public ProcessStepEdgeBuilder EmitExternalEvent(ProcessProxyBuilder proxyStep, string topicName)
    {
        // 1. Link sk event and topic
        proxyStep.LinkTopicToStepEdgeInfo(topicName, this.Source, this.EventData);

        // 2. Regular SK step link step functions/edge connection
        var targetBuilder = proxyStep.GetExternalFunctionTargetBuilder();

        return this.SendEventTo(targetBuilder);
    }

    /// <summary>
    /// Emit the SK step event as an external event with specific topic name
    /// </summary>
    /// <returns></returns>
    public ProcessStepEdgeBuilder SentToAgentStep(ProcessAgentBuilder agentStep)
    {
        var targetBuilder = agentStep.GetInvokeAgentFunctionTargetBuilder();

        return this.SendEventTo(targetBuilder);
    }

    /// <summary>
    /// Signals that the process should be stopped.
    /// </summary>
    public virtual void StopProcess()
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        var outputTarget = new ProcessFunctionTargetBuilder(EndStep.Instance);
        this.Target = outputTarget;
        this.Source.LinkTo(ProcessConstants.EndStepName, this);
    }
}
