// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public abstract class ProxyAgent : Agent
{
    private readonly Agent _agent;

    /// <inheritdoc/>
    public override string? Description => this._agent.Description;

    /// <inheritdoc/>
    public override string Id => this._agent.Id;

    /// <inheritdoc/>
    public override string? Name => this._agent.Name;

    /// <inheritdoc/>
    protected internal override Type ChannelType => this._agent.ChannelType;

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken) =>
        this._agent.CreateChannelAsync(cancellationToken);

    /// <summary>
    /// Initializes a new instance of the <see cref="ProxyAgent"/> class.
    /// </summary>
    /// <param name="agent">The agent</param>
    protected ProxyAgent(Agent agent)
    {
        this._agent = agent;
    }
}
