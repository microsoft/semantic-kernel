// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Presents an <see cref="AgentChat"/> as discrete agent.
/// </summary>
public sealed class AggregatorAgent : Agent
{
    private readonly AgentChat _chat;

    /// <inheritdoc/>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AggregatorChannel).FullName;
    }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new AggregatorChannel(this._chat));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AggregatorAgent"/> class.
    /// </summary>
    /// <param name="chat">An <see cref="AgentChat"/> instance.</param>
    public AggregatorAgent(AgentChat chat)
    {
        this._chat = chat;
    }

    /// <summary>
    /// Adapt channel contract to underlying <see cref="AgentChat"/>.
    /// </summary>
    private class AggregatorChannel : AgentChannel<AggregatorAgent>
    {
        private readonly AgentChat _chat;

        protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken = default)
        {
            return this._chat.GetChatMessagesAsync(cancellationToken);
        }

        protected internal override IAsyncEnumerable<ChatMessageContent> InvokeAsync(AggregatorAgent agent, CancellationToken cancellationToken = default)
        {
            return this._chat.InvokeAsync(cancellationToken); // %%% LAST / ALL / SOME
        }

        protected internal override Task ReceiveAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            this._chat.AddChatMessages(history.ToArray()); // %%% PARENT HISTORY (+ more)

            return Task.CompletedTask;
        }

        public AggregatorChannel(AgentChat chat)
        {
            this._chat = chat;
        }
    }
}
