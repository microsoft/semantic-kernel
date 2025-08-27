// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Graph.Models;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;
using TaskStatus = Microsoft.Graph.Models.TaskStatus;

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

/// <summary>
/// Connector for Microsoft To-Do API
/// </summary>
public class MicrosoftToDoConnector : ITaskManagementConnector
{
    private readonly GraphServiceClient _graphServiceClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="MicrosoftToDoConnector"/> class.
    /// </summary>
    /// <param name="graphServiceClient">A graph service client.</param>
    public MicrosoftToDoConnector(GraphServiceClient graphServiceClient)
    {
        this._graphServiceClient = graphServiceClient;
    }

    /// <inheritdoc/>
    public async Task<TaskManagementTaskList?> GetDefaultTaskListAsync(CancellationToken cancellationToken = default)
    {
        // .Filter("wellknownListName eq 'defaultList'") does not work as expected so we grab all the lists locally and filter them by name.
        // GH issue: https://github.com/microsoftgraph/microsoft-graph-docs/issues/17694

        // Get the initial page (response won't be null if successful; exceptions are thrown on failure)
        var initialPage = await this._graphServiceClient.Me.Todo.Lists.GetAsync(cancellationToken: cancellationToken).ConfigureAwait(false);

        TodoTaskList? result = null;

        if (initialPage is null)
        {
            return null;
        }

        var pageIterator = PageIterator<TodoTaskList, TodoTaskListCollectionResponse>.CreatePageIterator(
            this._graphServiceClient,
            initialPage,
            (list) =>
            {
                if (list?.WellknownListName == WellknownListName.DefaultList)
                {
                    result = list;
                    return false; // Stop iterating once found
                }
                return true; // Continue to next item/page
            });

        await pageIterator.IterateAsync(cancellationToken).ConfigureAwait(false);

        if (result is null)
        {
            return null; // No default list found
        }

        if (string.IsNullOrEmpty(result.Id))
        {
            return null; // Ensure the ID is not null or empty
        }

        return new TaskManagementTaskList(
            result.Id,  // We've checked it's not null/empty
            result.DisplayName ?? "Unnamed Default List"  // Coalesce to a fallback if null
        );
    }
    /// <inheritdoc/>
    public async Task<IEnumerable<TaskManagementTaskList>?> GetTaskListsAsync(CancellationToken cancellationToken = default)
    {
        // Get the initial page (response won't be null if successful; exceptions thrown on failure)
        var response = await this._graphServiceClient.Me.Todo.Lists
            .GetAsync(cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response?.Value == null)
        {
            return null;
        }

        List<TodoTaskList>? taskLists = null;

        var pageIterator = PageIterator<TodoTaskList, TodoTaskListCollectionResponse>.CreatePageIterator(
            this._graphServiceClient,
            response,
            (list) =>
            {
                (taskLists = []).Add(list);
                return true; // Continue to fetch all pages
            });

        await pageIterator.IterateAsync(cancellationToken).ConfigureAwait(false);

        return taskLists?.Select(list => new TaskManagementTaskList(
            id: list?.Id,
            name: list?.DisplayName));
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<TaskManagementTask>?> GetTasksAsync(string listId, bool includeCompleted, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));

        // Get the initial page with optional filter
        var response = await this._graphServiceClient.Me.Todo.Lists[listId].Tasks
            .GetAsync(requestConfig =>
            {
                if (!includeCompleted)
                {
                    requestConfig.QueryParameters.Filter = "status ne 'completed'";
                }
            }, cancellationToken).ConfigureAwait(false);

        if (response?.Value == null)
        {
            return Enumerable.Empty<TaskManagementTask>();
        }

        List<TodoTask>? tasks = null;

        var pageIterator = PageIterator<TodoTask, TodoTaskCollectionResponse>.CreatePageIterator(
            this._graphServiceClient,
            response,
            (task) =>
            {
                (tasks = []).Add(task);
                return true; // Continue to fetch all pages
            });

        await pageIterator.IterateAsync(cancellationToken).ConfigureAwait(false);

        return tasks?.Select(task => new TaskManagementTask(
            id: task?.Id,
            title: task?.Title,
            reminder: task?.ReminderDateTime?.DateTime,
            due: task?.DueDateTime?.DateTime,
            isCompleted: task?.Status == TaskStatus.Completed));
    }

    /// <inheritdoc/>
    public async Task<TaskManagementTask?> AddTaskAsync(string listId, TaskManagementTask task, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));
        Ensure.NotNull(task, nameof(task));

        var createdTask = await this._graphServiceClient.Me.Todo.Lists[listId].Tasks
            .PostAsync(FromTaskListTask(task), cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return createdTask != null ? ToTaskListTask(createdTask) : null;
    }

    /// <inheritdoc/>
    public Task DeleteTaskAsync(string listId, string taskId, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));
        Ensure.NotNullOrWhitespace(taskId, nameof(taskId));

        return this._graphServiceClient.Me
            .Todo.Lists[listId]
            .Tasks[taskId].DeleteAsync(cancellationToken: cancellationToken);
    }

    private static TodoTask FromTaskListTask(TaskManagementTask task)
    {
        Ensure.NotNull(task, nameof(task));

        return new TodoTask()
        {
            Title = task.Title,
            ReminderDateTime = task.Reminder is null
                ? null
                : DateTimeOffset.Parse(task.Reminder, CultureInfo.InvariantCulture.DateTimeFormat).ToDateTimeTimeZone(),
            DueDateTime = task.Due is null
                ? null
                : DateTimeOffset.Parse(task.Due, CultureInfo.InvariantCulture.DateTimeFormat).ToDateTimeTimeZone(),
            Status = task.IsCompleted ? TaskStatus.Completed : TaskStatus.NotStarted
        };
    }

    private static TaskManagementTask ToTaskListTask(TodoTask task)
    {
        Ensure.NotNull(task, nameof(task));

        return new TaskManagementTask(
            id: task.Id,
            title: task.Title,
            reminder: task.ReminderDateTime?.DateTime,
            due: task.DueDateTime?.DateTime,
            isCompleted: task.Status == TaskStatus.Completed);
    }
}
