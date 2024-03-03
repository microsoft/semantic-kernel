// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// Defines a strategy used by <see cref="StrategyNexus"/>.
/// </summary>
public abstract class SelectionStrategy
{
    private StrategyNexus? _nexus;

    /// <summary>
    /// The nexus bound to this strategy.
    /// </summary>
    protected StrategyNexus Nexus =>
        this._nexus ??
        throw new InvalidOperationException("Not bound to nexus");

    /// <summary>
    /// Identify the next agent for processing.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The next agent for processing.</returns>
    public abstract Task<KernelAgent> NextAgentAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Bind the nexus to this strategy.
    /// </summary>
    internal void Bind(StrategyNexus nexus)
    {
        if (this._nexus != null)
        {
            throw new AgentException("Already bound to nexus.");
        }

        this._nexus = nexus;
    }
}
