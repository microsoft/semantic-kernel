// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
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
public class CalendarSkill
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
    private readonly ILogger<CalendarSkill> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="CalendarSkill"/> class.
    /// </summary>
    /// <param name="connector">Calendar connector.</param>
    /// <param name="logger">Logger.</param>
    public CalendarSkill(ICalendarConnector connector, ILogger<CalendarSkill>? logger = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = logger ?? new NullLogger<CalendarSkill>();
    }

    /// <summary>
    /// Add an event to my calendar using <see cref="ContextVariables.Input"/> as the subject.
    /// </summary>
    [SKFunction("Add an event to my calendar.")]
    [SKFunctionInput(Description = "Event subject")]
    [SKFunctionContextParameter(Name = Parameters.Start, Description = "Event start date/time as DateTimeOffset")]
    [SKFunctionContextParameter(Name = Parameters.End, Description = "Event end date/time as DateTimeOffset")]
    [SKFunctionContextParameter(Name = Parameters.Location, Description = "Event location (optional)")]
    [SKFunctionContextParameter(Name = Parameters.Content, Description = "Event content/body (optional)")]
    [SKFunctionContextParameter(Name = Parameters.Attendees, Description = "Event attendees, separated by ',' or ';'.")]
    public async Task AddEventAsync(string subject, SKContext context)
    {
        ContextVariables variables = context.Variables;

        if (string.IsNullOrWhiteSpace(subject))
        {
            context.Fail("Missing variables input to use as event subject.");
            return;
        }

        if (!variables.Get(Parameters.Start, out string start))
        {
            context.Fail($"Missing variable {Parameters.Start}.");
            return;
        }

        if (!variables.Get(Parameters.End, out string end))
        {
            context.Fail($"Missing variable {Parameters.End}.");
            return;
        }

        CalendarEvent calendarEvent = new()
        {
            Subject = variables.Input,
            Start = DateTimeOffset.Parse(start, CultureInfo.InvariantCulture.DateTimeFormat),
            End = DateTimeOffset.Parse(end, CultureInfo.InvariantCulture.DateTimeFormat)
        };

        if (variables.Get(Parameters.Location, out string location))
        {
            calendarEvent.Location = location;
        }

        if (variables.Get(Parameters.Content, out string content))
        {
            calendarEvent.Content = content;
        }

        if (variables.Get(Parameters.Attendees, out string attendees))
        {
            calendarEvent.Attendees = attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
        }

        this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
        await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Get calendar events with specified optional clauses used to query for messages.
    /// </summary>
    [SKFunction("Get calendar events.")]
    [SKFunctionContextParameter(Name = Parameters.MaxResults, Description = "Optional limit of the number of events to retrieve.", DefaultValue = "10")]
    [SKFunctionContextParameter(Name = Parameters.Skip, Description = "Optional number of events to skip before retrieving results.", DefaultValue = "0")]
    public async Task<string> GetCalendarEventsAsync(SKContext context)
    {
        context.Variables.Get(Parameters.MaxResults, out string maxResultsString);
        context.Variables.Get(Parameters.Skip, out string skipString);
        this._logger.LogInformation("Getting calendar events with query options top: '{0}', skip:'{1}'.", maxResultsString, skipString);

        string selectString = "start,subject,organizer,location";

        int? top = null;
        if (!string.IsNullOrWhiteSpace(maxResultsString))
        {
            if (int.TryParse(maxResultsString, out int topValue))
            {
                top = topValue;
            }
        }

        int? skip = null;
        if (!string.IsNullOrWhiteSpace(skipString))
        {
            if (int.TryParse(skipString, out int skipValue))
            {
                skip = skipValue;
            }
        }

        IEnumerable<CalendarEvent> events = await this._connector.GetEventsAsync(
            top: top,
            skip: skip,
            select: selectString,
            context.CancellationToken
        ).ConfigureAwait(false);

        return JsonSerializer.Serialize(
            value: events,
            options: new JsonSerializerOptions
            {
                WriteIndented = false,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            });
    }
}
