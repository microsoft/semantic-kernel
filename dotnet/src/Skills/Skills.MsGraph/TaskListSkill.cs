// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
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
public class TaskListSkill
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
    [SKFunction("Add a task to a task list with an optional reminder.")]
    [SKFunctionInput(Description = "Title of the task.")]
    [SKFunctionContextParameter(Name = Parameters.Reminder, Description = "Reminder for the task in DateTimeOffset (optional)")]
    public async Task AddTaskAsync(string title, SKContext context)
    {
        TaskManagementTaskList? defaultTaskList = await this._connector.GetDefaultTaskListAsync(context.CancellationToken).ConfigureAwait(false);
        if (defaultTaskList == null)
        {
            context.Fail("No default task list found.");
            return;
        }

        TaskManagementTask task = new(
            id: Guid.NewGuid().ToString(),
            title: title);

        if (context.Variables.TryGetValue(Parameters.Reminder, out string? reminder))
        {
            task.Reminder = reminder;
        }

        this._logger.LogInformation("Adding task '{0}' to task list '{1}'", task.Title, defaultTaskList.Name);
        await this._connector.AddTaskAsync(defaultTaskList.Id, task, context.CancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get tasks from the default task list.
    /// </summary>
    [SKFunction("Get tasks from the default task list.")]
    [SKFunctionContextParameter(Name = Parameters.IncludeCompleted, Description = "Whether to include completed tasks (optional)", DefaultValue = "false")]
    public async Task<string> GetDefaultTasksAsync(SKContext context)
    {
        TaskManagementTaskList? defaultTaskList = await this._connector.GetDefaultTaskListAsync(context.CancellationToken)
            .ConfigureAwait(false);

        if (defaultTaskList == null)
        {
            context.Fail("No default task list found.");
            return string.Empty;
        }

        bool includeCompleted = false;
        if (context.Variables.TryGetValue(Parameters.IncludeCompleted, out string? includeCompletedString))
        {
            if (!bool.TryParse(includeCompletedString, out includeCompleted))
            {
                this._logger.LogWarning("Invalid value for '{0}' variable: '{1}'", Parameters.IncludeCompleted, includeCompletedString);
            }
        }

        IEnumerable<TaskManagementTask> tasks = await this._connector.GetTasksAsync(defaultTaskList.Id, includeCompleted, context.CancellationToken)
            .ConfigureAwait(false);

        return JsonSerializer.Serialize(tasks);
    }
}
