// Copyright (c) Microsoft. All rights reserved.
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

        if (this._index > agents.Count - 1)
        {
            this._index = 0;
        }

        var agent = agents[this._index];

        ++this._index;

        if (this._index == agents.Count)
        {
            this._index = 0;
        }

        return Task.FromResult<Agent?>(agent);
    }
}
