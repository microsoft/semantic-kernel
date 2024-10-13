// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public sealed class ProcessStepEdgeBuilder
{
    internal ProcessFunctionTargetBuilder? OutputTarget { get; private set; }
    internal ProcessFunctionTargetBuilder? Target { get; set; }

    /// <summary>
    /// The event Id that the edge fires on.
    /// </summary>
    internal string EventId { get; }

    /// <summary>
    /// The source step of the edge.
    /// </summary>
    internal ProcessStepBuilder Source { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    internal ProcessStepEdgeBuilder(ProcessStepBuilder source, string eventId)
    {
        Verify.NotNull(source);
        Verify.NotNullOrWhiteSpace(eventId);

        this.Source = source;
        this.EventId = eventId;
    }

    /// <summary>
    /// Builds the edge.
    /// </summary>
    internal KernelProcessEdge Build()
    {
        Verify.NotNull(this.Source?.Id);
        Verify.NotNull(this.OutputTarget);

        return new KernelProcessEdge(this.Source.Id, this.OutputTarget.Build());
        Verify.NotNull(this.Target);

        return new KernelProcessEdge(this.Source.Id, this.Target.Build());
    }

    /// <summary>
    /// Signals that the output of the source step should be sent to the specified target when the associated event fires.
    /// </summary>
    /// <param name="target">The output target.</param>
    /// <returns>A fresh builder instance for fluid definition</returns>
    public ProcessStepEdgeBuilder SendEventTo(ProcessFunctionTargetBuilder target)
    {
        if (this.OutputTarget is not null)
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        this.OutputTarget = outputTarget;
        this.Target = outputTarget;
        this.Target = target;
        this.Source.LinkTo(this.EventId, this);

        return new ProcessStepEdgeBuilder(this.Source, this.EventId);
    }

    /// <summary>
    /// Signals that the process should be stopped.
    /// </summary>
    public void StopProcess()
    {
        if (this.OutputTarget is not null)
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        var outputTarget = new ProcessFunctionTargetBuilder(EndStep.Instance);
        this.OutputTarget = outputTarget;
        this.Target = outputTarget;
        this.Source.LinkTo(EndStep.EndStepName, this);
    }
}
