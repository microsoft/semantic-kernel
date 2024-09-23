// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for incrementally defining a process edge.
/// </summary>
public class ProcessEdgeBuilder
{
    private readonly ProcessBuilder _source;
    private readonly string _eventId;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessEdgeBuilder"/> class.
    /// </summary>
    /// <param name="source">The source step.</param>
    /// <param name="eventId">The Id of the event.</param>
    internal ProcessEdgeBuilder(ProcessBuilder source, string eventId)
    {
        this._source = source;
        this._eventId = eventId;
    }

    /// <summary>
    /// Sends the output of the source step to the specified target when the associated event fires.
    /// </summary>
    /// <param name="outputTarget">The output target.</param>
    public void SendEventTo(ProcessStepEdgeBuilder outputTarget)
    {
        this._source.LinkTo(this._eventId, outputTarget);
    }
}
