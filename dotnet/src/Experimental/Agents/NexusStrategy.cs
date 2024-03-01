// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
public abstract class NexusStrategy
{
    private StrategyNexus? _nexus;

    /// <summary>
    /// $$$
    /// </summary>
    protected StrategyNexus Nexus =>
        this._nexus ??
        throw new InvalidOperationException("$$$");

    /// <summary>
    /// $$$
    /// </summary>
    /// <returns></returns>
    public abstract Task<KernelAgent> NextAgentAsync();

    internal void Bind(StrategyNexus chat)
    {
        if (this._nexus != null)
        {
            throw new InvalidOperationException("$$$");
        }

        this._nexus = chat;
    }
}
