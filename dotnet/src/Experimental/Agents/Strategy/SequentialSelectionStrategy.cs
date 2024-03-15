// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// Round-robin turn-taking strategy.
/// </summary>
public sealed class SequentialSelectionStrategy : SelectionStrategy
{
    private int _index = 0;

    /// <inheritdoc/>
    public override Task<Agent?> NextAgentAsync(CancellationToken cancellationToken)
    {
        var agent = this.Nexus.Agents[this._index];

        ++this._index;

        if (this._index == this.Nexus.Agents.Count)
        {
            this._index = 0;
        }

        return Task.FromResult<Agent?>(agent);
    }
}
