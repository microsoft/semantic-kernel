// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Models;

/// <summary>
/// Model for a list of tasks.
/// </summary>
public class TaskManagementTaskList
{
    /// <summary>
    /// ID of the task list.
    /// </summary>
    public string Id { get; set; }

    /// <summary>
    /// Name of the task list.
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TaskManagementTaskList"/> class.
    /// </summary>
    /// <param name="id">ID of the task list.</param>
    /// <param name="name">Name of the task list.</param>
    public TaskManagementTaskList(string id, string name)
    {
        this.Id = id;
        this.Name = name;
    }
}
