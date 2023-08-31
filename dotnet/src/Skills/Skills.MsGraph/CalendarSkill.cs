// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Skill for calendar operations.
/// </summary>
public sealed class CalendarSkill
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Event start as DateTimeOffset.
        /// </summary>
        public const string Start = "start";

        /// <summary>
        /// Event end as DateTimeOffset.
        /// </summary>
        public const string End = "end";

        /// <summary>
        /// Event's location.
        /// </summary>
        public const string Location = "location";

        /// <summary>
        /// Event's content.
        /// </summary>
        public const string Content = "content";

        /// <summary>
        /// Event's attendees, separated by ',' or ';'.
        /// </summary>
        public const string Attendees = "attendees";

        /// <summary>
        /// The name of the top parameter used to limit the number of results returned in the response.
        /// </summary>
        public const string MaxResults = "maxResults";

        /// <summary>
        /// The name of the skip parameter used to skip a certain number of results in the response.
        /// </summary>
        public const string Skip = "skip";
    }

    private readonly ICalendarConnector _connector;
    private readonly ILogger _logger;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="CalendarSkill"/> class.
    /// </summary>
    /// <param name="connector">Calendar connector.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public CalendarSkill(ICalendarConnector connector, ILoggerFactory? loggerFactory = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(CalendarSkill)) : NullLogger.Instance;
    }

    /// <summary>
    /// Add an event to my calendar using <see cref="ContextVariables.Input"/> as the subject.
    /// </summary>
    [SKFunction, Description("Add an event to my calendar.")]
    public async Task AddEventAsync(
        [Description("Event subject"), SKName("input")] string subject,
        [Description("Event start date/time as DateTimeOffset")] DateTimeOffset start,
        [Description("Event end date/time as DateTimeOffset")] DateTimeOffset end,
        [Description("Event location (optional)")] string? location = null,
        [Description("Event content/body (optional)")] string? content = null,
        [Description("Event attendees, separated by ',' or ';'.")] string? attendees = null)
    {
        if (string.IsNullOrWhiteSpace(subject))
        {
            throw new ArgumentException($"{nameof(subject)} variable was null or whitespace", nameof(subject));
        }

        CalendarEvent calendarEvent = new()
        {
            Subject = subject,
            Start = start,
            End = end,
            Location = location,
            Content = content,
            Attendees = attendees is not null ? attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries) : Enumerable.Empty<string>(),
        };

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Adding calendar event '{0}'", calendarEvent.Subject);
        await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Get calendar events with specified optional clauses used to query for messages.
    /// </summary>
    [SKFunction, Description("Get calendar events.")]
    public async Task<string> GetCalendarEventsAsync(
        [Description("Optional limit of the number of events to retrieve.")] int? maxResults = 10,
        [Description("Optional number of events to skip before retrieving results.")] int? skip = 0,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting calendar events with query options top: '{0}', skip:'{1}'.", maxResults, skip);

        const string SelectString = "start,subject,organizer,location";

        IEnumerable<CalendarEvent> events = await this._connector.GetEventsAsync(
            top: maxResults,
            skip: skip,
            select: SelectString,
            cancellationToken
        ).ConfigureAwait(false);

        return JsonSerializer.Serialize(value: events, options: s_options);
    }
}
