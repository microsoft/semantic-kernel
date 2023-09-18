// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Models;

/// <summary>
/// Model for a calendar event.
/// </summary>
public class CalendarEvent
{
    /// <summary>
    /// Subject/title of the event.
    /// </summary>
    public string? Subject { get; set; }

    /// <summary>
    /// Body/content of the event.
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Start time of the event.
    /// </summary>
    public DateTimeOffset? Start { get; set; }

    /// <summary>
    /// End time of the event.
    /// </summary>
    public DateTimeOffset? End { get; set; }

    /// <summary>
    /// Location of the event.
    /// </summary>
    public string? Location { get; set; }

    /// <summary>
    /// Attendees of the event.
    /// </summary>
    public IEnumerable<string>? Attendees { get; set; } = Enumerable.Empty<string>();
}
