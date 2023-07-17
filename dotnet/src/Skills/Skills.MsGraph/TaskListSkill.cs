// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json;
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
/// Task list skill (e.g. Microsoft To-Do)
/// </summary>
public sealed class TaskListSkill
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Task reminder as DateTimeOffset.
        /// </summary>
        public const string Reminder = "reminder";

        /// <summary>
        /// Whether to include completed tasks.
        /// </summary>
        public const string IncludeCompleted = "includeCompleted";
    }

    private readonly ITaskManagementConnector _connector;
    private readonly ILogger<TaskListSkill> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="TaskListSkill"/> class.
    /// </summary>
    /// <param name="connector">Task list connector.</param>
    /// <param name="logger">Logger.</param>
    public TaskListSkill(ITaskManagementConnector connector, ILogger<TaskListSkill>? logger = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = logger ?? new NullLogger<TaskListSkill>();
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
    [SKFunction, Description("Add a task to a task list with an optional reminder.")]
    public async Task AddTaskAsync(
        [Description("Title of the task.")] string title,
        [Description("Reminder for the task in DateTimeOffset (optional)")] string? reminder = null,
        CancellationToken cancellationToken = default)
    {
        TaskManagementTaskList? defaultTaskList = await this._connector.GetDefaultTaskListAsync(cancellationToken).ConfigureAwait(false);
        if (defaultTaskList == null)
        {
            throw new InvalidOperationException("No default task list found.");
        }

        TaskManagementTask task = new(
            id: Guid.NewGuid().ToString(),
            title: title,
            reminder: reminder);

        this._logger.LogInformation("Adding task '{0}' to task list '{1}'", task.Title, defaultTaskList.Name);
        await this._connector.AddTaskAsync(defaultTaskList.Id, task, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get tasks from the default task list.
    /// </summary>
    [SKFunction, Description("Get tasks from the default task list.")]
    public async Task<string> GetDefaultTasksAsync(
        [Description("Whether to include completed tasks (optional)")] string includeCompleted = "false",
        CancellationToken cancellationToken = default)
    {
        TaskManagementTaskList? defaultTaskList = await this._connector.GetDefaultTaskListAsync(cancellationToken).ConfigureAwait(false);
        if (defaultTaskList == null)
        {
            throw new InvalidOperationException("No default task list found.");
        }

        if (!bool.TryParse(includeCompleted, out bool includeCompletedValue))
        {
            this._logger.LogWarning("Invalid value for '{0}' variable: '{1}'", nameof(includeCompleted), includeCompleted);
        }

        IEnumerable<TaskManagementTask> tasks = await this._connector.GetTasksAsync(defaultTaskList.Id, includeCompletedValue, cancellationToken).ConfigureAwait(false);
        return JsonSerializer.Serialize(tasks);
    }
}
