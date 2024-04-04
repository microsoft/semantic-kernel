// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A an <see cref="AgentNexus"/> that supports multi-turn interactions.
/// </summary>
public sealed class AgentChat : AgentNexus
{
    private readonly HashSet<string> _agentIds; // Efficient existence test
    private readonly List<Agent> _agents; // Maintain order (fwiw)

    /// <summary>
    /// Indicates if completion criteria has been met.  If set, no further
    /// agent interactions will occur.  Clear to enable more agent interactions.
    /// </summary>
    public bool IsComplete { get; set; }

    /// <summary>
    /// Settings for defining chat behavior.
    /// </summary>
    public ChatExecutionSettings? ExecutionSettings { get; set; }

    /// <summary>
    /// The agents participating in the nexus.
    /// </summary>
    public IReadOnlyList<Agent> Agents => this._agents.AsReadOnly();

    /// <summary>
    /// Add a <see cref="Agent"/> to the nexus.
    /// </summary>
    /// <param name="agent">The <see cref="KernelAgent"/> to add.</param>
    public void AddAgent(Agent agent)
    {
        if (this._agentIds.Add(agent.Id))
        {
            this._agents.Add(agent);
        }
    }

    /// <summary>
    /// Process a single interaction between a given <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this.IsComplete)
        {
            yield break;
        }

        // Use the the count, if defined and positive, otherwise use default maximum (1).
        var maximumIterations = Math.Max(this.ExecutionSettings?.MaximumIterations ?? 0, ChatExecutionSettings.DefaultMaximumIterations);

        var selectionStrategy = this.ExecutionSettings?.SelectionStrategy;
        if (selectionStrategy == null)
        {
            yield break;
        }

        for (int index = 0; index < maximumIterations; index++)
        {
            // Identify next agent using strategy
            var agent = await selectionStrategy.Invoke(this.Agents, this.History, cancellationToken).ConfigureAwait(false);
            if (agent == null)
            {
                yield break;
            }

            await foreach (var message in base.InvokeAgentAsync(agent, cancellationToken))
            {
                yield return message;

                if (message.Role == AuthorRole.Assistant)
                {
                    // Null ExecutionSettings short-circuits prior to this due to null SelectionStrategy.
                    var task = this.ExecutionSettings!.TerminationStrategy?.Invoke(agent, this.History, cancellationToken) ?? Task.FromResult(false);
                    this.IsComplete = await task.ConfigureAwait(false);
                }

                if (this.IsComplete)
                {
                    break;
                }
            }

            if (this.IsComplete)
            {
                break;
            }
        }
    }

    /// <summary>
    /// Process a single interaction between a given <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remark>
    /// Specified agent joins the nexus.
    /// </remark>>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        CancellationToken cancellationToken = default) =>
        this.InvokeAsync(agent, isJoining: true, cancellationToken);

    /// <summary>
    /// Process a single interaction between a given <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="isJoining">Optional flag to control if agent is joining the nexus.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        bool isJoining,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (isJoining)
        {
            this.AddAgent(agent);
        }

        await foreach (var message in base.InvokeAgentAsync(agent, cancellationToken))
        {
            yield return message;

            if (message.Role == AuthorRole.Assistant)
            {
                var task = this.ExecutionSettings?.TerminationStrategy?.Invoke(agent, this.History, cancellationToken) ?? Task.FromResult(false);
                this.IsComplete = await task.ConfigureAwait(false);
            }

            if (this.IsComplete)
            {
                break;
            }
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChat"/> class.
    /// </summary>
    /// <param name="agents">The agents initially participating in the nexus.</param>
    public AgentChat(params Agent[] agents)
    {
        this._agents = new(agents);
        this._agentIds = new(this._agents.Select(a => a.Id));
    }
}
