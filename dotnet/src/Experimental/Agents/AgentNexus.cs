// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Associate a <see cref="ChatMessageContent"/> with an agent source.
/// </summary>
/// <param name="AgentId">The agent identifier</param>
/// <param name="MessageId">An optional message identifier.</param>
public record AgentMessageSource(string AgentId, string? MessageId = null)
{
    internal string ToJson()
    {
        return BinaryData.FromObjectAsJson(this).ToString();
    }
}

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
public abstract class AgentNexus /*: $$$ TODO: PLUGIN ??? */
{
    private readonly Dictionary<Type, AgentChannel> _agentChannels;

    /// <summary>
    /// The primary nexus history.
    /// </summary>
    internal ChatHistory History { get; }

    /// <summary>
    /// Retrieve the message history, either the primary history or
    /// an agent specific version.
    /// </summary>
    /// <param name="agent">An optional agent, if requesting an agent history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    public IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(KernelAgent? agent = null, CancellationToken cancellationToken = default)
    {
        if (agent == null)
        {
            return this.History.Reverse().ToAsyncEnumerable();
        }

        if (!this._agentChannels.TryGetValue(agent.ChannelType, out var channel))
        {
            return Array.Empty<ChatMessageContent>().ToAsyncEnumerable();
        }

        return channel.GetHistoryAsync(cancellationToken);
    }

    /// <summary>
    /// Transform text into a user message.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    protected static ChatMessageContent? CreateUserMessage(string? input)
    {
        return string.IsNullOrWhiteSpace(input) ? null : new ChatMessageContent(AuthorRole.User, input);
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    protected async IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(
        KernelAgent agent,
        ChatMessageContent? input = null,
        /*KernelArguments $$$ TODO: TEMPLATING,*/
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Verify only a single operation is active
        int isActive = 0;
        int wasActive = Interlocked.CompareExchange(ref isActive, 1, 0);
        if (wasActive > 0)
        {
            throw new AgentException("Unable to proceed while another agent is active.");
        }

        // Manifest the required channel
        var channel = await this.GetChannelAsync(agent, cancellationToken).ConfigureAwait(false);

        // Invoke agent & process response
        await foreach (var message in channel.InvokeAsync(agent, input, cancellationToken).ConfigureAwait(false))
        {
            this.History.Add(message);

            yield return message;

            var tasks =
                this._agentChannels.Values
                    .Where(c => c != channel)
                    .Select(c => c.RecieveAsync([message]));

            await Task.WhenAll(tasks).ConfigureAwait(false);
        }
    }

    private async Task<AgentChannel> GetChannelAsync(KernelAgent agent, CancellationToken cancellationToken)
    {
        // $$$ TODO: BETTER KEY THAN TYPE (DIFFERENT APIKEYS / ENDPOINTS / TENENTS OF SAME TYPE)
        if (!this._agentChannels.TryGetValue(agent.ChannelType, out var channel))
        {
            channel = await agent.CreateChannelAsync(this, cancellationToken).ConfigureAwait(false);

            if (this.History.Count > 0)
            {
                await channel.RecieveAsync(this.History, cancellationToken).ConfigureAwait(false);
            }

            this._agentChannels.Add(agent.ChannelType, channel);
        }

        return channel;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentNexus"/> class.
    /// </summary>
    protected AgentNexus()
    {
        this._agentChannels = [];
        this.History = [];
    }
}
