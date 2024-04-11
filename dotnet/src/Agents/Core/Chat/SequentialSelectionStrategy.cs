// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

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
    public void Reset()
        => this._index = 0;

    /// <inheritdoc/>
    public override Task<Agent> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        if (agents.Count == 0)
        {
            throw new KernelException("Agent Failure - No agents present to select.");
        }

        var agent = agents[this._index % agents.Count];

        try
        {
            // If overflow occurs, a runtime exception will be raised (checked).
            this._index = checked(this._index + 1);
        }
        catch (Exception exception) when (!exception.IsCriticalException())
        {
            this._index = (int.MaxValue % agents.Count) + 1; // Maintain proper next agent
        }

        return Task.FromResult(agent);
    }
}
