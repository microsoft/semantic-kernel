// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
public abstract class AgentNexus /*: $$$ ChatHistory ??? */
{
    private readonly Dictionary<Type, AgentChannel> _agentChannels;

    internal ChatHistory History { get; }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    protected IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(KernelAgent agent, string? input = null, /*KernelArguments $$$,*/ CancellationToken cancellationToken = default)
    {
        var content = string.IsNullOrWhiteSpace(input) ? null : new ChatMessageContent(AuthorRole.User, input);
        return this.InvokeAgentAsync(agent, content, cancellationToken);
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
        /*KernelArguments $$$,*/
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // $$$ CONCURRENCY

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
        // $$$ BETTER KEY THAN TYPE (DIFFERENT APIKEYS / ENDPOINTS / TENENTS OF SAME TYPE)
        if (!this._agentChannels.TryGetValue(agent.ChannelType, out var channel))
        {
            // $$$ CHANNEL FACTORY (CREATE / RESTORE) - CONTEXT
            channel = await agent.CreateChannelAsync(this, cancellationToken).ConfigureAwait(false);

            if (this.History.Count > 0)
            {
                await channel.RecieveAsync(this.History, cancellationToken).ConfigureAwait(false); // $$$ NEED SYNC-POINT FOR RESTORE
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
