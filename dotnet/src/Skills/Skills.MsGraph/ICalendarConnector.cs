// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Interface for calendar connections (e.g. Outlook).
/// </summary>
public interface ICalendarConnector
{
    /// <summary>
    /// Add a new event to the user's calendar
    /// </summary>
    /// <param name="calendarEvent">Event to add.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Event that was added.</returns>
    Task<CalendarEvent> AddEventAsync(CalendarEvent calendarEvent, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the user's calendar events.
    /// </summary>
    /// <param name="top">How many events to get.</param>
    /// <param name="skip">How many events to skip.</param>
    /// <param name="select">Optionally select which event properties to get.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The user's calendar events.</returns>
#pragma warning disable CA1716 // Identifiers should not match keywords
    Task<IEnumerable<CalendarEvent>> GetEventsAsync(int? top, int? skip, string? @select, CancellationToken cancellationToken = default);
#pragma warning restore CA1716 // Identifiers should not match keywords
}
