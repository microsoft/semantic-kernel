// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Round-robin turn-taking strategy.  Agent order is based on the order
/// in which they joined <see cref="AgentGroupChat"/>.
/// </summary>
public sealed class SequentialSelectionStrategy : SelectionStrategy
{
    private int _index = 0;

    /// <summary>
    /// Reset selection to initial/first agent. Agent order is based on the order
    /// in which they joined <see cref="AgentGroupChat"/>.
    /// </summary>
    public void Reset() => this._index = 0;

    /// <inheritdoc/>
    public override Task<Agent> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        if (agents.Count == 0)
        {
            throw new KernelException("Agent Failure - No agents present to select.");
        }

        // Set of agents array may not align with previous execution, constrain index to valid range.
        if (this._index > agents.Count - 1)
        {
            this._index = 0;
        }

        if (this.Logger.IsEnabled(LogLevel.Debug)) // Avoid boxing if not enabled
        {
            this.Logger.LogDebug("[{MethodName}] Prior agent index: {AgentIndex} / {AgentCount}.", nameof(NextAsync), this._index, agents.Count);
        }

        var agent = agents[this._index];

        this._index = (this._index + 1) % agents.Count;

        if (this.Logger.IsEnabled(LogLevel.Information)) // Avoid boxing if not enabled
        {
            this.Logger.LogInformation("[{MethodName}] Current agent index: {AgentIndex} / {AgentCount}", nameof(NextAsync), this._index, agents.Count);
        }

        return Task.FromResult(agent);
    }
}
