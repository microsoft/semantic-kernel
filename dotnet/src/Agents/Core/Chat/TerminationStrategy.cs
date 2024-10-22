// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for defining termination criteria for a <see cref="AgentGroupChat"/>.
/// </summary>
public abstract class TerminationStrategy
{
    /// <summary>
    /// Restrict number of turns to a reasonable number (99).
    /// </summary>
    public const int DefaultMaximumIterations = 99;

    /// <summary>
    /// The maximum number of agent interactions for a given chat invocation.
    /// Defaults to: <see cref="TerminationStrategy.DefaultMaximumIterations"/>.
    /// </summary>
    public int MaximumIterations { get; set; } = DefaultMaximumIterations;

    /// <summary>
    /// Set to have automatically clear <see cref="AgentGroupChat.IsComplete"/> if caller
    /// proceeds with invocation subsequent to achieving termination criteria.
    /// </summary>
    public bool AutomaticReset { get; set; }

    /// <summary>
    /// Set of agents for which this strategy is applicable.  If not set,
    /// any agent is evaluated.
    /// </summary>
    public IReadOnlyList<Agent>? Agents { get; set; }

    /// <summary>
    /// The <see cref="ILogger"/> associated with the <see cref="TerminationStrategy"/>.
    /// </summary>
    protected internal ILogger Logger { get; internal set; } = NullLogger.Instance;

    /// <summary>
    /// Called to evaluate termination once <see cref="TerminationStrategy.Agents"/> is evaluated.
    /// </summary>
    protected abstract Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

    /// <summary>
    /// Evaluate the input message and determine if the chat has met its completion criteria.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="history">The most recent message</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True to terminate chat loop.</returns>
    public async Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this.Logger.LogTerminationStrategyEvaluatingCriteria(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id);

        // `Agents` must contain `agent`, if `Agents` not empty.
        if ((this.Agents?.Count ?? 0) > 0 && !this.Agents!.Any(a => a.Id == agent.Id))
        {
            this.Logger.LogTerminationStrategyAgentOutOfScope(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id);

            return false;
        }

        bool shouldTerminate = await this.ShouldAgentTerminateAsync(agent, history, cancellationToken).ConfigureAwait(false);

        this.Logger.LogTerminationStrategyEvaluatedCriteria(nameof(ShouldTerminateAsync), agent.GetType(), agent.Id, shouldTerminate);

        return shouldTerminate;
    }
}
