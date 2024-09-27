// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

/// <summary>
/// Connector for Outlook Calendar API
/// </summary>
public class OutlookCalendarConnector : ICalendarConnector
{
    private readonly GraphServiceClient _graphServiceClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="OutlookCalendarConnector"/> class.
    /// </summary>
    /// <param name="graphServiceClient">A graph service client.</param>
    public OutlookCalendarConnector(GraphServiceClient graphServiceClient)
    {
        this._graphServiceClient = graphServiceClient;
    }

    /// <inheritdoc/>
    public async Task<CalendarEvent> AddEventAsync(CalendarEvent calendarEvent, CancellationToken cancellationToken = default)
    {
        Event resultEvent = await this._graphServiceClient.Me.Events.Request()
            .AddAsync(calendarEvent.ToGraphEvent(), cancellationToken).ConfigureAwait(false);
        return resultEvent.ToCalendarEvent();
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<CalendarEvent>> GetEventsAsync(
        int? top, int? skip, string? select, CancellationToken cancellationToken = default)
    {
        ICalendarEventsCollectionRequest query = this._graphServiceClient.Me.Calendar.Events.Request();

        if (top.HasValue)
        {
            query.Top(top.Value);
        }

        if (skip.HasValue)
        {
            query.Skip(skip.Value);
        }

        if (!string.IsNullOrEmpty(select))
        {
            query.Select(select);
        }

        ICalendarEventsCollectionPage result = await query.GetAsync(cancellationToken).ConfigureAwait(false);

        IEnumerable<CalendarEvent> events = result.Select(e => e.ToCalendarEvent());

        return events;
    }
}
