// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Strategy;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// Delegate definition for <see cref="NexusExecutionSettings.CompletionCriteria"/>.
/// </summary>
/// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
/// <returns>True when complete.</returns>
public delegate IAsyncEnumerable<ChatMessageContent> NexusInvocationCallback(CancellationToken cancellationToken);

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class NexusAgent : Agent
{
    private readonly NexusInvocationCallback _invocationCallback;

    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <inheritdoc/>
    protected internal override Type ChannelType => typeof(LocalChannel<NexusAgent>);

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new LocalChannel<NexusAgent>(nexus, InvokeAsync));
    }

    private static async IAsyncEnumerable<ChatMessageContent> InvokeAsync(NexusAgent agent, ChatHistory chat, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var message in agent._invocationCallback.Invoke(cancellationToken))
        {
            yield return message;
        }

        // $$$ SUMMARIZE ???
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="invocationCallback">Callback for invoking a nexus.</param>
    /// <param name="description">The agent description (optional)</param>
    /// <param name="name">The agent name</param>
    public NexusAgent(
        NexusInvocationCallback invocationCallback,
        string? description = null,
        string? name = null)
    {
        this.Id = Guid.NewGuid().ToString();
        this._invocationCallback = invocationCallback;
        this.Description = description;
        this.Name = name;
    }
}
