// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public sealed class ProcessStepEdgeBuilder
{
    internal ProcessFunctionTargetBuilder? Target { get; set; }

    /// <summary>
    /// The event Id that the edge fires on.
    /// Unique event Id linked to the source id.
    /// </summary>
    internal string EventId { get; }

    /// <summary>
    /// The event name that the edge fires on.
    /// </summary>
    internal string EventName { get; }

    /// <summary>
    /// The source step of the edge.
    /// </summary>
    internal ProcessStepBuilder Source { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    /// <param name="eventName">The name of the event</param>
    internal ProcessStepEdgeBuilder(ProcessStepBuilder source, string eventId, string eventName)
    {
        Verify.NotNull(source);
        Verify.NotNullOrWhiteSpace(eventId);
        Verify.NotNullOrWhiteSpace(eventName);

        this.Source = source;
        this.EventId = eventId;
        this.EventName = eventName;
    }

    /// <summary>
    /// Builds the edge.
    /// </summary>
    internal KernelProcessEdge Build()
    {
        Verify.NotNull(this.Source?.Id);
        Verify.NotNull(this.Target);

        return new KernelProcessEdge(this.Source.Id, this.Target.Build(), this.EventName, this.EventId);
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo(ProcessFunctionTargetBuilder target)
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        this.Target = target;
        this.Source.LinkTo(this.EventId, this);

        return new ProcessStepEdgeBuilder(this.Source, this.EventId, this.EventName);
    }

    /// <summary>
    /// Forward specific step events to process events so specific functions linked get executed
    /// when receiving the specific event
    /// </summary>
    /// <param name="processEdge"></param>
    /// <returns></returns>
    public ProcessStepEdgeBuilder EmitAsProcessEvent(ProcessEdgeBuilder processEdge)
    {
        processEdge.Source._eventsSubscriber?.LinkStepEventToProcessEvent(this.EventId, processEventId: processEdge.EventId);

        return new ProcessStepEdgeBuilder(this.Source, this.EventId, this.EventName);
    }

    /// <summary>
    /// Signals that the process should be stopped.
    /// </summary>
    public void StopProcess()
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
