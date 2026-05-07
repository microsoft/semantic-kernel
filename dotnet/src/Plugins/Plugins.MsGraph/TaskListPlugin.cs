// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
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
/// Task list plugin (e.g. Microsoft To-Do)
/// </summary>
public sealed class TaskListPlugin
{
    private readonly ITaskManagementConnector _connector;
    private readonly ILogger _logger;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="TaskListPlugin"/> class.
    /// </summary>
    /// <param name="connector">Task list connector.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization. If null, default options will be used.</param>
    public TaskListPlugin(ITaskManagementConnector connector, ILoggerFactory? loggerFactory = null, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._jsonSerializerOptions = jsonSerializerOptions ?? s_options;
        this._connector = connector;
        this._logger = loggerFactory?.CreateLogger(typeof(TaskListPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Calculates an upcoming day of week (e.g. 'next Monday').
    /// </summary>
    public static DateTimeOffset GetNextDayOfWeek(DayOfWeek dayOfWeek, TimeSpan timeOfDay)
    {
        DateTimeOffset today = new(DateTime.Today);
        int nextDayOfWeekOffset = dayOfWeek - today.DayOfWeek;
        if (nextDayOfWeekOffset <= 0)
        {
            nextDayOfWeekOffset += 7;
        }

        DateTimeOffset nextDayOfWeek = today.AddDays(nextDayOfWeekOffset);
        DateTimeOffset nextDayOfWeekAtTimeOfDay = nextDayOfWeek.Add(timeOfDay);

        return nextDayOfWeekAtTimeOfDay;
    }

    /// <summary>
    /// Add a task to a To-Do list with an optional reminder.
    /// </summary>
    [KernelFunction, Description("Add a task to a task list with an optional reminder.")]
    public async Task AddTaskAsync(
        [Description("Title of the task.")] string title,
        [Description("Reminder for the task in DateTimeOffset (optional)")] string? reminder = null,
        CancellationToken cancellationToken = default)
    {
        TaskManagementTaskList defaultTaskList = await this._connector.GetDefaultTaskListAsync(cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("No default task list found.");

        TaskManagementTask task = new(
            id: Guid.NewGuid().ToString(),
            title: title,
            reminder: reminder);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Adding task '{0}' to task list '{1}'", task.Title, defaultTaskList.Name);

        await this._connector.AddTaskAsync(defaultTaskList.Id!, task, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get tasks from the default task list.
    /// </summary>
    [KernelFunction, Description("Get tasks from the default task list.")]
    public async Task<string?> GetDefaultTasksAsync(
        [Description("Whether to include completed tasks (optional)")] string includeCompleted = "false",
        CancellationToken cancellationToken = default)
    {
        TaskManagementTaskList defaultTaskList = await this._connector.GetDefaultTaskListAsync(cancellationToken).ConfigureAwait(false) ??
            throw new InvalidOperationException("No default task list found.");

        if (!bool.TryParse(includeCompleted, out bool includeCompletedValue))
        {
            this._logger.LogWarning("Invalid value for '{0}' variable: '{1}'", nameof(includeCompleted), includeCompleted);
        }

        IEnumerable<TaskManagementTask>? tasks = await this._connector.GetTasksAsync(defaultTaskList.Id!, includeCompletedValue, cancellationToken).ConfigureAwait(false);
        return JsonSerializer.Serialize(tasks, s_options);
    }
}
