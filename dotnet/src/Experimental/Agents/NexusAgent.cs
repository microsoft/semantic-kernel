// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class NexusAgent : KernelAgent<LocalChannel<NexusAgent>>
{
    private readonly AgentNexus _nexus;

    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new LocalChannel<NexusAgent>(this._nexus, NexusAgent.InvokeAsync)); // $$$ WHICH NEXUS ???
    }

    private static async IAsyncEnumerable<ChatMessageContent> InvokeAsync(NexusAgent agent, ChatHistory chat, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var message in ((AgentChat)agent._nexus).InvokeAsync(input: default(string), cancellationToken)) // $$$ HACK CAST
        {
            yield return message;
        }
        // $$$ SUMMARIZE
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="nexus"></param>
    /// <param name="description"></param>
    /// <param name="name"></param>
    public NexusAgent(
        AgentNexus nexus,
        string? description = null,
        string? name = null)
       : base(Kernel.CreateBuilder().Build()) // $$$
    {
        this.Id = Guid.NewGuid().ToString();
        this._nexus = nexus;
        this.Description = description;
        this.Name = name;
    }
}
