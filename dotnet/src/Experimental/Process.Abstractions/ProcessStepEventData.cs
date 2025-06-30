// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents data associated with a process step event.
/// </summary>
public record ProcessStepEventData
{
    /// <summary>
    /// Gets the unique identifier for the event. Recommended to be human readable and unique within the process.
    /// </summary>
    public string EventId { get; init; } = string.Empty;

    /// <summary>
    /// Determines whether the event is public outside the step parent process or not.
    /// </summary>
    public bool IsPublic { get; set; } = false;

    /// <summary>
    /// Gets the event type data associated with the process event.
    /// </summary>
    public KernelEventTypeData? EventTypeData { get; init; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessStepEventData"/> class with the specified event ID and
    /// optional event type data.
    /// </summary>
    /// <param name="eventId">The unique identifier for the event. This value cannot be null or empty.</param>
    /// <param name="eventTypeData">Optional data describing the type of the event. If not provided, the event type data will be null.</param>
    public ProcessStepEventData(string eventId, KernelEventTypeData? eventTypeData = null)
    {
        this.EventId = eventId;
        this.EventTypeData = eventTypeData;
    }
}
