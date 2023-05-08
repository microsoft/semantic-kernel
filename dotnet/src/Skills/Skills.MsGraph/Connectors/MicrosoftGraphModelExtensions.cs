// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Graph;
using Microsoft.Graph.Extensions;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors;

/// <summary>
/// Extensions for converting between Microsoft Graph models and skill models.
/// </summary>
internal static class MicrosoftGraphModelExtensions
{
    /// <summary>
    /// Convert a Microsoft Graph message to an email message.
    /// </summary>
    public static Models.EmailMessage ToEmailMessage(this Message graphMessage)
        => new()
        {
            BccRecipients = graphMessage.BccRecipients?.Select(r => r.EmailAddress.ToEmailAddress()),
            Body = graphMessage.Body?.Content,
            BodyPreview = graphMessage.BodyPreview.Replace("\u200C", ""), // BodyPreviews are sometimes filled with zero-width non-joiner characters - remove them.
            CcRecipients = graphMessage.CcRecipients?.Select(r => r.EmailAddress.ToEmailAddress()),
            From = graphMessage.From?.EmailAddress?.ToEmailAddress(),
            IsRead = graphMessage.IsRead,
            ReceivedDateTime = graphMessage.ReceivedDateTime,
            Recipients = graphMessage.ToRecipients?.Select(r => r.EmailAddress.ToEmailAddress()),
            SentDateTime = graphMessage.SentDateTime,
            Subject = graphMessage.Subject
        };

    /// <summary>
    /// Convert a Microsoft Graph email address to an email address.
    /// </summary>
    public static Models.EmailAddress ToEmailAddress(this Microsoft.Graph.EmailAddress graphEmailAddress)
        => new()
        {
            Address = graphEmailAddress.Address,
            Name = graphEmailAddress.Name
        };

    /// <summary>
    /// Convert a calendar event to a Microsoft Graph event.
    /// </summary>
    public static Graph.Event ToGraphEvent(this CalendarEvent calendarEvent)
        => new()
        {
            Subject = calendarEvent.Subject,
            Body = new ItemBody { Content = calendarEvent.Content, ContentType = BodyType.Html },
            Start = calendarEvent.Start.HasValue
                ? DateTimeTimeZone.FromDateTimeOffset(calendarEvent.Start.Value)
                : DateTimeTimeZone.FromDateTime(System.DateTime.Now),
            End = calendarEvent.End.HasValue
                ? DateTimeTimeZone.FromDateTimeOffset(calendarEvent.End.Value)
                : DateTimeTimeZone.FromDateTime(System.DateTime.Now + TimeSpan.FromHours(1)),
            Location = new Location { DisplayName = calendarEvent.Location },
            Attendees = calendarEvent.Attendees?.Select(a => new Attendee { EmailAddress = new Microsoft.Graph.EmailAddress { Address = a } })
        };

    /// <summary>
    /// Convert a Microsoft Graph event to a calendar event.
    /// </summary>
    public static Models.CalendarEvent ToCalendarEvent(this Event msGraphEvent)
        => new()
        {
            Subject = msGraphEvent.Subject,
            Content = msGraphEvent.Body?.Content,
            Start = msGraphEvent.Start?.ToDateTimeOffset(),
            End = msGraphEvent.End?.ToDateTimeOffset(),
            Location = msGraphEvent.Location?.DisplayName,
            Attendees = msGraphEvent.Attendees?.Select(a => a.EmailAddress.Address)
        };
}
