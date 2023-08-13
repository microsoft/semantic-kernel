// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents a common base class to record Timestamps and duration
/// </summary>
public class TestEvent
{
    /// <summary>
    /// Gets or sets the timestamp of the test event.
    /// </summary>
    public DateTime Timestamp { get; set; } = DateTime.Now;

    /// <summary>
    /// Gets or sets the duration of the test event.
    /// </summary>
    public TimeSpan Duration { get; set; }
}
