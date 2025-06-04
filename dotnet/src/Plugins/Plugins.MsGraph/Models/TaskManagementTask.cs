// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Models;

/// <summary>
/// Model for a task in a task list.
/// </summary>
public class TaskManagementTask
{
    /// <summary>
    /// ID of the task.
    /// </summary>
    public string Id { get; set; }

    /// <summary>
    /// Title of the task.
    /// </summary>
    public string Title { get; set; }

    /// <summary>
    /// Reminder date/time for the task.
    /// </summary>
    public string? Reminder { get; set; }

    /// <summary>
    /// Task's due date/time.
    /// </summary>
    public string? Due { get; set; }

    /// <summary>
    /// True if the task is completed, otherwise false.
    /// </summary>
    public bool IsCompleted { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TaskManagementTask"/> class.
    /// </summary>
    /// <param name="id">ID of the task.</param>
    /// <param name="title">Title of the task.</param>
    /// <param name="reminder">Reminder date/time for the task.</param>
    /// <param name="due">Task's due date/time.</param>
    /// <param name="isCompleted">True if the task is completed, otherwise false.</param>
    public TaskManagementTask(string id, string title, string? reminder = null, string? due = null, bool isCompleted = false)
    {
        this.Id = id;
        this.Title = title;
        this.Reminder = reminder;
        this.Due = due;
        this.IsCompleted = isCompleted;
    }
}
