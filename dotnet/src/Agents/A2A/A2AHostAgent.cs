// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using A2A;

namespace Microsoft.SemanticKernel.Agents.A2A;

/// <summary>
/// Host which will attach a <see cref="A2AAgent"/> to a <see cref="ITaskManager"/>
/// </summary>
public sealed class A2AHostAgent
{
    /// <summary>
    /// Initializes a new instance of the SemanticKernelTravelAgent
    /// </summary>
    public A2AHostAgent(Agent agent, AgentCard agentCard, TaskManager? taskManager = null)
    {
        Verify.NotNull(agent);
        Verify.NotNull(agentCard);

        this.Agent = agent;
        this._agentCard = agentCard;

        this.Attach(taskManager ?? new TaskManager());
    }

    /// <summary>
    /// The associated <see cref="Agent"/>
    /// </summary>
    public Agent? Agent { get; private set; }

    /// <summary>
    /// The associated <see cref="ITaskManager"/>
    /// </summary>
    public TaskManager? TaskManager => this._taskManager;

    /// <summary>
    /// Attach the <see cref="A2AAgent"/> to the provided <see cref="ITaskManager"/>
    /// </summary>
    /// <param name="taskManager"></param>
    public void Attach(TaskManager taskManager)
    {
        Verify.NotNull(taskManager);

        this._taskManager = taskManager;
        taskManager.OnTaskCreated = this.ExecuteAgentTaskAsync;
        taskManager.OnTaskUpdated = this.ExecuteAgentTaskAsync;
        taskManager.OnAgentCardQuery = this.GetAgentCardAsync;
    }
    /// <summary>
    /// Execute the specific <see cref="AgentTask"/>
    /// </summary>
    /// <param name="task">The <see cref="AgentTask"/> to execute</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to cancel the operation</param>
    /// <exception cref="Exception"></exception>
    public async Task ExecuteAgentTaskAsync(AgentTask task, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(task);
        Verify.NotNull(this.Agent);

        if (this._taskManager is null)
        {
            throw new InvalidOperationException("TaskManager must be attached before executing an agent task.");
        }

        await this._taskManager.UpdateStatusAsync(task.Id, TaskState.Working, cancellationToken: cancellationToken).ConfigureAwait(false);

        // Get message from the user
        var userMessage = task.History!.Last().Parts.First().AsTextPart().Text;

        // Get the response from the agent
        var artifact = new Artifact();
        await foreach (AgentResponseItem<ChatMessageContent> response in this.Agent.InvokeAsync(userMessage, cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            var content = response.Message.Content;
            artifact.Parts.Add(new TextPart() { Text = content! });
        }

        // Return as artifacts
        await this._taskManager.ReturnArtifactAsync(task.Id, artifact, cancellationToken).ConfigureAwait(false);
        await this._taskManager.UpdateStatusAsync(task.Id, TaskState.Completed, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the <see cref="AgentCard"/> associated with this hosted agent.
    /// </summary>
    /// <param name="agentUrl">Current URL for the agent</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to cancel the operation</param>
#pragma warning disable CA1054 // URI-like parameters should not be strings
    public async Task<AgentCard> GetAgentCardAsync(string agentUrl, CancellationToken cancellationToken)
    {
        // Ensure the URL is in the correct format
        Uri uri = new(agentUrl);
        agentUrl = $"{uri.Scheme}://{uri.Host}:{uri.Port}/";

        this._agentCard.Url = agentUrl;
        return this._agentCard;
    }
#pragma warning restore CA1054 // URI-like parameters should not be strings

    #region private
    private readonly AgentCard _agentCard;
    private TaskManager? _taskManager;
    #endregion
}
