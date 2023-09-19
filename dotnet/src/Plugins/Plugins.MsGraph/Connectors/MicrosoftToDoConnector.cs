// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;
using TaskStatus = Microsoft.Graph.TaskStatus;

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

        ITodoListsCollectionPage lists = await this._graphServiceClient.Me
            .Todo.Lists
            .Request().GetAsync(cancellationToken).ConfigureAwait(false);

        TodoTaskList? result = lists.SingleOrDefault(list => list.WellknownListName == WellknownListName.DefaultList);

        while (result == null && lists.Count != 0 && lists.NextPageRequest != null)
        {
            lists = await lists.NextPageRequest.GetAsync(cancellationToken).ConfigureAwait(false);
            result = lists.SingleOrDefault(list => list.WellknownListName == WellknownListName.DefaultList);
        }

        if (result == null)
        {
            throw new SKException("Could not find default task list.");
        }

        return new TaskManagementTaskList(result.Id, result.DisplayName);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<TaskManagementTaskList>> GetTaskListsAsync(CancellationToken cancellationToken = default)
    {
        ITodoListsCollectionPage lists = await this._graphServiceClient.Me
            .Todo.Lists
            .Request().GetAsync(cancellationToken).ConfigureAwait(false);

        List<TodoTaskList> taskLists = lists.ToList();

        while (lists.Count != 0 && lists.NextPageRequest != null)
        {
            lists = await lists.NextPageRequest.GetAsync(cancellationToken).ConfigureAwait(false);
            taskLists.AddRange(lists.ToList());
        }

        return taskLists.Select(list => new TaskManagementTaskList(
            id: list.Id,
            name: list.DisplayName));
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<TaskManagementTask>> GetTasksAsync(string listId, bool includeCompleted, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));

        string filterValue = string.Empty;
        if (!includeCompleted)
        {
            filterValue = "status ne 'completed'";
        }

        ITodoTaskListTasksCollectionPage tasksPage = await this._graphServiceClient.Me
            .Todo.Lists[listId]
            .Tasks.Request().Filter(filterValue).GetAsync(cancellationToken).ConfigureAwait(false);

        List<TodoTask> tasks = tasksPage.ToList();

        while (tasksPage.Count != 0 && tasksPage.NextPageRequest != null)
        {
            tasksPage = await tasksPage.NextPageRequest.GetAsync(cancellationToken).ConfigureAwait(false);
            tasks.AddRange(tasksPage.ToList());
        }

        return tasks.Select(task => new TaskManagementTask(
            id: task.Id,
            title: task.Title,
            reminder: task.ReminderDateTime?.DateTime,
            due: task.DueDateTime?.DateTime,
            isCompleted: task.Status == TaskStatus.Completed));
    }

    /// <inheritdoc/>
    public async Task<TaskManagementTask> AddTaskAsync(string listId, TaskManagementTask task, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));
        Ensure.NotNull(task, nameof(task));

        return ToTaskListTask(await this._graphServiceClient.Me
            .Todo.Lists[listId]
            .Tasks
            .Request().AddAsync(FromTaskListTask(task), cancellationToken).ConfigureAwait(false));
    }

    /// <inheritdoc/>
    public Task DeleteTaskAsync(string listId, string taskId, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(listId, nameof(listId));
        Ensure.NotNullOrWhitespace(taskId, nameof(taskId));

        return this._graphServiceClient.Me
            .Todo.Lists[listId]
            .Tasks[taskId]
            .Request().DeleteAsync(cancellationToken);
    }

    private static TodoTask FromTaskListTask(TaskManagementTask task)
    {
        Ensure.NotNull(task, nameof(task));

        return new TodoTask()
        {
            Title = task.Title,
            ReminderDateTime = task.Reminder == null
                ? null
                : DateTimeTimeZone.FromDateTimeOffset(DateTimeOffset.Parse(task.Reminder, CultureInfo.InvariantCulture.DateTimeFormat)),
            DueDateTime = task.Due == null
                ? null
                : DateTimeTimeZone.FromDateTimeOffset(DateTimeOffset.Parse(task.Due, CultureInfo.InvariantCulture.DateTimeFormat)),
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
