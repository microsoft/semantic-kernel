// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Defines a strategy used by <see cref="StrategyNexus"/>.
/// </summary>
public abstract class NexusStrategy
{
    private StrategyNexus? _nexus;

    /// <summary>
    /// The nexus bound to this strategy.
    /// </summary>
    protected StrategyNexus Nexus =>
        this._nexus ??
        throw new InvalidOperationException("$$$");

    /// <summary>
    /// Identify the next agent for processing.
    /// </summary>
    /// <returns>The next agent for processing.</returns>
    public abstract Task<KernelAgent> NextAgentAsync();

    /// <summary>
    /// Bind the nexus to this strategy.
    /// </summary>
    internal void Bind(StrategyNexus nexus)
    {
        if (this._nexus != null)
        {
            throw new InvalidOperationException("$$$");
        }

        this._nexus = nexus;
    }
}
