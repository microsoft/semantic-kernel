// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the relationship between the internal aggregated chat and the chat
/// with which <see cref="AggregatorAgent"/> is participating.
/// </summary>
[Experimental("SKEXP0110")]
public enum AggregatorMode
{
    /// <summary>
    /// A flat embedding of the aggregated chat within another chat.
    /// </summary>
    Flat,

    /// <summary>
    /// A nested embedding the aggregated chat within another chat.
    /// </summary>
    Nested,
}

/// <summary>
/// Allows an <see cref="AgentChat"/> to participate in another <see cref="AgentChat"/> as an <see cref="Agent"/>.
/// </summary>
/// <param name="chatProvider">A factory method that produces a new <see cref="AgentChat"/> instance.</param>
[Experimental("SKEXP0110")]
public sealed class AggregatorAgent(Func<AgentChat> chatProvider) : Agent
{
    /// <summary>
    /// Gets the relationship between the internal aggregated chat and the chat
    /// with which <see cref="AggregatorAgent"/> is participating.
    /// </summary>
    /// <value>
    /// The relationship between the internal aggregated chat and the chat
    /// with which <see cref="AggregatorAgent"/> is participating. The default value is <see cref="AggregatorMode.Flat"/>.
    /// </value>
    public AggregatorMode Mode { get; init; } = AggregatorMode.Flat;

    /// <inheritdoc/>
    public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        // TODO: Need to determine the correct approach here.
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        // TODO: Need to determine the correct approach here.
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    /// <remarks>
    /// Different <see cref="AggregatorAgent"/> instances will never share the same channel.
    /// </remarks>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AggregatorChannel).FullName!;
        yield return this.Name ?? this.Id;
    }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogAggregatorAgentCreatingChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel));

        AgentChat chat = chatProvider.Invoke();
        AggregatorChannel channel = new(chat);

        this.Logger.LogAggregatorAgentCreatedChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel), this.Mode, chat.GetType());

        return Task.FromResult<AgentChannel>(channel);
    }

    /// <inheritdoc/>
    protected internal async override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        this.Logger.LogOpenAIAssistantAgentRestoringChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel));

        AgentChat chat = chatProvider.Invoke();
        AgentChatState agentChatState =
            JsonSerializer.Deserialize<AgentChatState>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");

        await chat.DeserializeAsync(agentChatState).ConfigureAwait(false); ;
        AggregatorChannel channel = new(chat);

        this.Logger.LogOpenAIAssistantAgentRestoredChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel));

        return channel;
    }
}
