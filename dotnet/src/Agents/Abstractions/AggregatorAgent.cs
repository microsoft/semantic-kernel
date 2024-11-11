﻿// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the relationship between the internal aggregated chat and the chat
/// with which <see cref="AggregatorAgent"/> is participating.
/// </summary>
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
public sealed class AggregatorAgent(Func<AgentChat> chatProvider) : Agent
{
    /// <summary>
    /// Defines the relationship between the internal aggregated chat and the chat
    /// with which <see cref="AggregatorAgent"/> is participating.
    /// Default: <see cref="AggregatorMode.Flat"/>.
    /// </summary>
    public AggregatorMode Mode { get; init; } = AggregatorMode.Flat;

    /// <inheritdoc/>
    /// <remarks>
    /// Different <see cref="AggregatorAgent"/> will never share the same channel.
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
