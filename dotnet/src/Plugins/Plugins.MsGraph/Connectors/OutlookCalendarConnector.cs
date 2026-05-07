// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Graph.Models;
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
    public async Task<CalendarEvent?> AddEventAsync(CalendarEvent calendarEvent, CancellationToken cancellationToken = default)
    {
        Event? resultEvent = await this._graphServiceClient.Me.Events
            .PostAsync(calendarEvent.ToGraphEvent(), cancellationToken: cancellationToken).ConfigureAwait(false);

        return resultEvent?.ToCalendarEvent();
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<CalendarEvent>?> GetEventsAsync(
        int? top, int? skip, string? select, CancellationToken cancellationToken = default)
    {
        var result = await this._graphServiceClient.Me.Calendar.Events.GetAsync(config =>
        {
            config.QueryParameters.Top = top;
            config.QueryParameters.Skip = skip;
            config.QueryParameters.Select = !string.IsNullOrEmpty(select) ? [select] : null;
        }, cancellationToken: cancellationToken).ConfigureAwait(false);

        IEnumerable<CalendarEvent>? events = result?.Value?.Select(e => e.ToCalendarEvent());

        return events;
    }
}
