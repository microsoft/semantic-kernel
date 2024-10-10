// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Threading;
using System.Threading.Tasks;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Threading;
using System.Threading.Tasks;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
using System.Threading;
using System.Threading.Tasks;
=======
>>>>>>> Stashed changes
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Serialization;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

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
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AggregatorChannel).FullName!;
    }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogAggregatorAgentCreatingChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel));
>>>>>>>-Updated upstrea
ebug("[{MethodName}] Creating channel {ChannelType}", nameof(CreateChannelAsync), nameof(AggregatorChannel));
        this.Logger.LogDebug("[{MethodName}] Creating channel {ChannelType}", nameof(CreateChannelAsync), nameof(AggregatorChannel));

        AgentChat chat = chatProvider.Invoke();
        AggregatorChannel channel = new(chat);

        this.Logger.LogAggregatorAgentCreatedChannel(nameof(CreateChannelAsync), nameof(AggregatorChannel), this.Mode, chat.GetType());
        this.Logger.LogInformation("[{MethodName}] Created channel {ChannelType} ({ChannelMode}) with: {AgentChatType}", nameof(CreateChannelAsync), nameof(AggregatorChannel), this.Mode, chat.GetType());

        return Task.FromResult<AgentChannel>(channel);
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
