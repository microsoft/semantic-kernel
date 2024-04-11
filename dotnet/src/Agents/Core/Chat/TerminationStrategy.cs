// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for defining termination criteria for a <see cref="AgentGroupChat"/>.
/// </summary>
public abstract class TerminationStrategy
{
    /// <summary>
    /// Set of agents for which this strategy is applicable.  If not set,
    /// any agent is evaluated.
    /// </summary>
    public IReadOnlyList<Agent>? Agents { get; set; }

    /// <summary>
    /// Implicitly convert a <see cref="TerminationStrategy"/> to a <see cref="TerminationCriteriaCallback"/>.
    /// </summary>
    /// <param name="strategy">A <see cref="TerminationStrategy"/> instance.</param>
    public static implicit operator TerminationCriteriaCallback(TerminationStrategy strategy)
    {
        return strategy.ShouldTerminateAsync;
    }

    /// <summary>
    /// Called to evaluate termination once <see cref="TerminationStrategy.Agents"/> is evaluated.
    /// </summary>
    protected abstract Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);

    /// <summary>
    /// Evaluate the input message and determine if the chat has met its completion criteria.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="history">The most recent message</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True to terminate chat loop.</returns>
    public Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // `Agents` must contain `agent`, if `Agents` not empty.
        if ((this.Agents?.Count ?? 0) > 0 && !this.Agents!.Any(a => a.Id == agent.Id))
        {
            return Task.FromResult(false);
        }

        return this.ShouldAgentTerminateAsync(agent, history, cancellationToken);
    }
}
