// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
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
        ContextVariables memory = context.Variables;

        if (string.IsNullOrWhiteSpace(subject))
        {
            context.Fail($"Missing variables input to use as event subject.");
            return;
        }

        if (!memory.Get(Parameters.Start, out string start))
        {
            context.Fail($"Missing variable {Parameters.Start}.");
            return;
        }

        if (!memory.Get(Parameters.End, out string end))
        {
            context.Fail($"Missing variable {Parameters.End}.");
            return;
        }

        CalendarEvent calendarEvent = new CalendarEvent(
            memory.Input,
            DateTimeOffset.Parse(start, CultureInfo.InvariantCulture.DateTimeFormat),
            DateTimeOffset.Parse(end, CultureInfo.InvariantCulture.DateTimeFormat));

        if (memory.Get(Parameters.Location, out string location))
        {
            calendarEvent.Location = location;
        }

        if (memory.Get(Parameters.Content, out string content))
        {
            calendarEvent.Content = content;
        }

        if (memory.Get(Parameters.Attendees, out string attendees))
        {
            calendarEvent.Attendees = attendees.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
        }

        this._logger.LogInformation("Adding calendar event '{0}'", calendarEvent.Subject);
        await this._connector.AddEventAsync(calendarEvent);
    }
}
