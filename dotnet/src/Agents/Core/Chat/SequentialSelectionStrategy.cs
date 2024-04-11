// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Round-robin turn-taking strategy.
/// </summary>
public sealed class SequentialSelectionStrategy : SelectionStrategy
{
    private int _index = 0;

    /// <inheritdoc/>
    public override Task<Agent?> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        if (agents.Count == 0)
        {
            return Task.FromResult<Agent?>(null);
        }

        var agent = agents[this._index % agents.Count];

        try
        {
            // If overflow occurs, a runtime exception will be raised (checked).
            this._index = checked(this._index + 1);
        }
        catch (Exception exception) when (!exception.IsCriticalException())
        {
            this._index = (int.MaxValue % agents.Count) + 1;
        }

        return Task.FromResult<Agent?>(agent);
    }
}
