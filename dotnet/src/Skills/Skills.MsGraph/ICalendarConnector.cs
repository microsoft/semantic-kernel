// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Event that was added.</returns>
    Task<CalendarEvent> AddEventAsync(CalendarEvent calendarEvent, CancellationToken cancellationToken = default);
}
