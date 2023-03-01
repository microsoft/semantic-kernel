// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Graph.Extensions;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors;

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
        Event resultEvent = await this._graphServiceClient.Me.Events.Request().AddAsync(ToGraphEvent(calendarEvent), cancellationToken);
        return ToCalendarEvent(resultEvent);
    }

    private static Event ToGraphEvent(CalendarEvent calendarEvent)
        => new Event()
        {
            Subject = calendarEvent.Subject,
            Body = new ItemBody { Content = calendarEvent.Content, ContentType = BodyType.Html },
            Start = DateTimeTimeZone.FromDateTimeOffset(calendarEvent.Start),
            End = DateTimeTimeZone.FromDateTimeOffset(calendarEvent.End),
            Location = new Location { DisplayName = calendarEvent.Location },
            Attendees = calendarEvent.Attendees?.Select(a => new Attendee { EmailAddress = new EmailAddress { Address = a } })
        };

    private static CalendarEvent ToCalendarEvent(Event msGraphEvent)
        => new CalendarEvent(msGraphEvent.Subject, msGraphEvent.Start.ToDateTimeOffset(), msGraphEvent.End.ToDateTimeOffset())
        {
            Id = msGraphEvent.Id,
            Content = msGraphEvent.Body?.Content,
            Location = msGraphEvent.Location?.DisplayName,
            Attendees = msGraphEvent.Attendees?.Select(a => a.EmailAddress.Address)
        };
}
