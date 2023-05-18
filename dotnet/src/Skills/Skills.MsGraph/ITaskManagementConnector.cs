// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Interface for task list connections (e.g. Microsoft To-Do).
/// </summary>
public interface ITaskManagementConnector
{
    /// <summary>
    /// Add a task to the specified list.
    /// </summary>
    /// <param name="listId">ID of the list in which to add the task.</param>
    /// <param name="task">Task to add.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Added task definition.</returns>
    Task<TaskManagementTask> AddTaskAsync(string listId, TaskManagementTask task, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a task from a task list.
    /// </summary>
    /// <param name="listId">ID of the list from which to delete the task.</param>
    /// <param name="taskId">ID of the task to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteTaskAsync(string listId, string taskId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the default task list.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<TaskManagementTaskList?> GetDefaultTaskListAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all the task lists.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>All of the user's task lists.</returns>
    Task<IEnumerable<TaskManagementTaskList>> GetTaskListsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the all tasks in a task list.
    /// </summary>
    /// <param name="listId">ID of the list from which to get the tasks.</param>
    /// <param name="includeCompleted">Whether to include completed tasks.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>All of the tasks in the specified task list.</returns>
    Task<IEnumerable<TaskManagementTask>> GetTasksAsync(string listId, bool includeCompleted, CancellationToken cancellationToken = default);
}
