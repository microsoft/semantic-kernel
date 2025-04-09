// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Extensions;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Provides a base strategy class for defining termination criteria for an <see cref="AgentGroupChat"/>.
/// </summary>
[Experimental("SKEXP0110")]
public abstract class TerminationStrategy
{
    /// <summary>
    /// Specifies a reasonable limit on the number of turns.
    /// </summary>
    public const int DefaultMaximumIterations = 99;

    /// <summary>
    /// Gets or sets the maximum number of agent interactions for a given chat invocation.
    /// </summary>
    /// <value>
    /// The default is <see cref="TerminationStrategy.DefaultMaximumIterations"/>.
    /// </value>
    public int MaximumIterations { get; set; } = DefaultMaximumIterations;

    /// <summary>
    /// Gets or sets a value that indicates whether <see cref="AgentGroupChat.IsComplete"/>
    /// is automatically cleared if the caller
    /// proceeds with invocation subsequent to achieving termination criteria.
    /// </summary>
    public bool AutomaticReset { get; set; }

    /// <summary>
    /// Gets or sets the set of agents for which this strategy is applicable.
    /// </summary>
    /// <value>
    /// The default value is that any agent is evaluated.
    /// </value>
    public IReadOnlyList<Agent>? Agents { get; set; }

    /// <summary>
    /// Gets the <see cref="ILogger"/> associated with the <see cref="TerminationStrategy"/>.
    /// </summary>
    protected internal ILogger Logger { get; internal set; } = NullLogger.Instance;

    /// <summary>
    /// Evaluates termination once <see cref="TerminationStrategy.Agents"/> is evaluated.
    /// </summary>
    protected abstract Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

    /// <summary>
    /// Evaluates the input message and determines if the chat has met its completion criteria.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="history">The most recent message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns><see langword="true"/> if the chat loop should be terminated.</returns>
    public async Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this.Logger.LogTerminationStrategyEvaluatingCriteria(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id, agent.GetDisplayName());

        // `Agents` must contain `agent`, if `Agents` not empty.
        if ((this.Agents?.Count ?? 0) > 0 && !this.Agents!.Any(a => a.Id == agent.Id))
        {
            this.Logger.LogTerminationStrategyAgentOutOfScope(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id, agent.GetDisplayName());

            return false;
        }

        bool shouldTerminate = await this.ShouldAgentTerminateAsync(agent, history, cancellationToken).ConfigureAwait(false);

        this.Logger.LogTerminationStrategyEvaluatedCriteria(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id, agent.GetDisplayName(), shouldTerminate);

        return shouldTerminate;
    }
}
