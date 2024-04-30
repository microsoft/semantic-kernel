// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Adapt channel contract to underlying <see cref="AgentChat"/>.
/// </summary>
internal class AggregatorChannel(AgentChat chat) : AgentChannel<AggregatorAgent>
{
    private readonly AgentChat _chat = chat;

    protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken = default)
    {
        return this._chat.GetChatMessagesAsync(cancellationToken);
    }

    protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(AggregatorAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatMessageContent? lastMessage = null;

        await foreach (ChatMessageContent message in this._chat.InvokeAsync(cancellationToken).ConfigureAwait(false))
        {
            if (agent.Mode == AggregatorMode.Flat)
            {
                yield return message;
            }

            lastMessage = message;
        }

        if (agent.Mode == AggregatorMode.Hiearchical && lastMessage != null)
        {
            ChatMessageContent message =
                new(lastMessage.Role, lastMessage.Items, lastMessage.ModelId, lastMessage.InnerContent, lastMessage.Encoding, lastMessage.Metadata)
                {
                    AuthorName = agent.Name
                };

            yield return message;
        }
    }

    protected internal override Task ReceiveAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this._chat.AddChatMessages([.. history]);

        return Task.CompletedTask;
    }
}
