// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Filters strategy evaluation according to a set of agents.
/// </summary>
public abstract class AgentBoundTerminationStrategy : TerminationStrategy
{
    /// <summary>
    /// Set of agents for which this strategy is applicable.
    /// </summary>
    public IReadOnlyList<Agent>? Agents { get; set; }

    /// <inheritdoc/>
    public sealed override Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Agent must match, if specified.
        if ((this.Agents?.Count ?? 0) > 0 && !this.Agents!.Any(a => a.Id == agent.Id))
        {
            return Task.FromResult(false);
        }

        return this.ShouldAgentTerminateAsync(agent, history, cancellationToken);
    }

    /// <summary>
    /// Called when the agent is known to match the binding.
    /// </summary>
    protected abstract Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken);
}
