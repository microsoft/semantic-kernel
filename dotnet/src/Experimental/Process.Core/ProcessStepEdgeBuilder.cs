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
    internal ProcessFunctionTargetBuilder? Target { get; set; }

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
    /// Initializes a new instance of the <see cref="ProcessStepEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    /// <param name="eventName"></param>
    /// <param name="edgeGroupBuilder">The group Id for the edge.</param>
    internal ProcessStepEdgeBuilder(ProcessStepBuilder source, string eventId, string eventName, KernelProcessEdgeGroupBuilder? edgeGroupBuilder = null)
    {
        Verify.NotNull(source, nameof(source));
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        this.Source = source;
        this.EventData = new() { EventId = eventId, EventName = eventName };
        this.EdgeGroupBuilder = edgeGroupBuilder;
    }

    /// <summary>
    /// Builds the edge.
    /// </summary>
    internal KernelProcessEdge Build(ProcessBuilder? processBuilder = null)
    {
        Verify.NotNull(this.Source?.Id);
        Verify.NotNull(this.Target);

        if (this.EdgeGroupBuilder is not null && this.Target is ProcessStepTargetBuilder stepTargetBuilder)
        {
            var messageSources = this.EdgeGroupBuilder.MessageSources.Select(e => new KernelProcessMessageSource(e.MessageType, e.Source.Id)).ToList();
            var edgeGroup = new KernelProcessEdgeGroup(this.EdgeGroupBuilder.GroupId, messageSources, stepTargetBuilder.InputMapping);
            this.Target.Step.RegisterGroupInputMapping(edgeGroup);
        }

        return new KernelProcessEdge(this.Source.Id, this.Target.Build(processBuilder), groupId: this.EdgeGroupBuilder?.GroupId);
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo(ProcessFunctionTargetBuilder target)
    {
        return this.SendEventTo_Internal(target);
    }

    /// <summary>
    /// Internally overridable implementation: Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    /// <exception cref="InvalidOperationException"></exception>
    /// <exception cref="ArgumentException"></exception>
    internal virtual ProcessStepEdgeBuilder SendEventTo_Internal(ProcessFunctionTargetBuilder target)
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        if (this.Source is ProcessMapBuilder && target.Step is ProcessMapBuilder)
        {
            throw new ArgumentException($"{nameof(ProcessMapBuilder)} may not target another {nameof(ProcessMapBuilder)}.", nameof(target));
        }

        this.Target = target;
        this.Source.LinkTo(this.EventData.EventId, this);

        return new ProcessStepEdgeBuilder(this.Source, this.EventData.EventId, this.EventData.EventName, this.EdgeGroupBuilder);
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
