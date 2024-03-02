// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Round-robin turn-taking strategy.
/// </summary>
public sealed class SequentialChatStrategy : NexusStrategy
{
    private int _index = 0;

    /// <inheritdoc/>
    public override Task<KernelAgent> NextAgentAsync()
    {
        ++this._index;

        if (this._index == this.Nexus.Agents.Count)
        {
            this._index = 0;
        }

        return Task.FromResult(this.Nexus.Agents[this._index]);
    }
}
