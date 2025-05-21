// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public sealed class ProcessEdgeBuilder : ProcessStepEdgeBuilder
{
    /// <summary>
    /// The source step of the edge.
    /// </summary>
    internal new ProcessBuilder Source { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    internal ProcessEdgeBuilder(ProcessBuilder source, string eventId) : base(source, eventId, eventId)
    {
        this.Source = source;
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    public ProcessEdgeBuilder SendEventTo(ProcessFunctionTargetBuilder target, Dictionary<string, object?>? metadata = null)
    {
        return this.SendEventTo(target as ProcessTargetBuilder, metadata);
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    public new ProcessEdgeBuilder SendEventTo(ProcessTargetBuilder target, Dictionary<string, object?>? metadata = null)
    {
        return this.SendEventTo(target as ProcessTargetBuilder);
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    public new ProcessEdgeBuilder SendEventTo(ProcessTargetBuilder target)
    {
        if (this.Target is not null)
        {
            throw new InvalidOperationException("An output target has already been set.");
        }

        this.Target = target;
        ProcessStepEdgeBuilder edgeBuilder = new(this.Source, this.EventData.EventId, this.EventData.EventId) { Target = this.Target };
        this.Source.LinkTo(this.EventData.EventId, edgeBuilder);

        return new ProcessEdgeBuilder(this.Source, this.EventData.EventId);
    }
}
