﻿// Copyright (c) Microsoft. All rights reserved.

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
using Microsoft.SemanticKernel.Plugins.MsGraph.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;

namespace Microsoft.SemanticKernel.Plugins.MsGraph;

/// <summary>
/// Plugin for calendar operations.
/// </summary>
public sealed class CalendarPlugin
{
    private readonly ICalendarConnector _connector;
    private readonly ILogger _logger;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
    private static readonly char[] s_separator = [',', ';'];

    /// <summary>
    /// Initializes a new instance of the <see cref="CalendarPlugin"/> class.
    /// </summary>
    /// <param name="connector">Calendar connector.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization. If null, default options will be used.</param>
    public CalendarPlugin(ICalendarConnector connector, ILoggerFactory? loggerFactory = null, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._jsonSerializerOptions = jsonSerializerOptions ?? s_options;

        this._connector = connector;
        this._logger = loggerFactory?.CreateLogger(typeof(CalendarPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Add an event to my calendar.
    /// </summary>
    [KernelFunction, Description("Add an event to my calendar.")]
    public async Task AddEventAsync(
        [Description("Event subject")] string input,
        [Description("Event start date/time as DateTimeOffset")] DateTimeOffset start,
        [Description("Event end date/time as DateTimeOffset")] DateTimeOffset end,
        [Description("Event location (optional)")] string? location = null,
        [Description("Event content/body (optional)")] string? content = null,
        [Description("Event attendees, separated by ',' or ';'.")] string? attendees = null)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            throw new ArgumentException($"{nameof(input)} variable was null or whitespace", nameof(input));
        }

        CalendarEvent calendarEvent = new()
        {
            Subject = input,
            Start = start,
            End = end,
            Location = location,
            Content = content,
            Attendees = attendees is not null ? attendees.Split(s_separator, StringSplitOptions.RemoveEmptyEntries) : Enumerable.Empty<string>(),
        };

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Adding calendar event '{0}'", calendarEvent.Subject);
        await this._connector.AddEventAsync(calendarEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Get calendar events with specified optional clauses used to query for messages.
    /// </summary>
    [KernelFunction, Description("Get calendar events.")]
    public async Task<string> GetCalendarEventsAsync(
        [Description("Optional limit of the number of events to retrieve.")] int? maxResults = 10,
        [Description("Optional number of events to skip before retrieving results.")] int? skip = 0,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting calendar events with query options top: '{0}', skip:'{1}'.", maxResults, skip);

        const string SelectString = "start,subject,organizer,location";

        IEnumerable<CalendarEvent>? events = await this._connector.GetEventsAsync(
            top: maxResults,
            skip: skip,
            select: SelectString,
            cancellationToken
        ).ConfigureAwait(false);

        return JsonSerializer.Serialize(value: events, options: this._jsonSerializerOptions);
    }
}
