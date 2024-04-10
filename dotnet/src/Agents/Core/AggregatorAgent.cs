// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

///// <summary>
///// Delegate definition for <see cref="NexusExecutionSettings.CompletionCriteria"/>.
///// </summary>
///// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
///// <returns>True when complete.</returns>
//public delegate IAsyncEnumerable<ChatMessageContent> NexusInvocationCallback(CancellationToken cancellationToken);

/// <summary>
/// $$$
/// </summary>
public sealed class AggregatorAgent : Agent, IChatHistoryHandler
{
    private readonly AgentGroupChat _chat; // $$$ INTERFACE??? 

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(ChatHistoryChannel).FullName;
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel());
    }

    /// <inheritdoc/>
    async IAsyncEnumerable<ChatMessageContent> IChatHistoryHandler.InvokeAsync(
        IReadOnlyList<ChatMessageContent> history,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await foreach (var message in this._chat.InvokeAsync(cancellationToken))
        {
            yield return message;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="chat">The underlying chat.</param>
    /// <param name="description">The agent description (optional)</param>
    /// <param name="name">The agent name</param>
    public AggregatorAgent(
        AgentGroupChat chat,
        string? description = null,
        string? name = null)
    {
        this._chat = chat;

        this.Id = Guid.NewGuid().ToString();
        this.Description = description;
        this.Name = name;
    }
}
