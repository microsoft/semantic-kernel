// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Adapt channel contract to underlying <see cref="AgentChat"/>.
/// </summary>
[Experimental("SKEXP0110")]
internal sealed class AggregatorChannel(AgentChat chat) : AgentChannel<AggregatorAgent>
{
    private readonly AgentChat _chat = chat;

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken = default)
    {
        return this._chat.GetChatMessagesAsync(cancellationToken);
    }

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(AggregatorAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatMessageContent? lastMessage = null;

        await foreach (ChatMessageContent message in this._chat.InvokeAsync(cancellationToken).ConfigureAwait(false))
        {
            // For AggregatorMode.Flat, the entire aggregated chat is merged into the owning chat.
            if (agent.Mode == AggregatorMode.Flat)
            {
                yield return (IsVisible: true, message);
            }

            lastMessage = message;
        }

        // For AggregatorMode.Nested, only the final message is merged into the owning chat.
        // The entire history is always preserved within nested chat, however.
        if (agent.Mode == AggregatorMode.Nested && lastMessage is not null)
        {
            ChatMessageContent message =
                new(lastMessage.Role, lastMessage.Items, lastMessage.ModelId, lastMessage.InnerContent, lastMessage.Encoding, lastMessage.Metadata)
                {
                    AuthorName = agent.Name
                };

            yield return (IsVisible: true, message);
        }
    }

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(AggregatorAgent agent, IList<ChatMessageContent> messages, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        int initialCount = await this._chat.GetChatMessagesAsync(cancellationToken).CountAsync(cancellationToken).ConfigureAwait(false);

        await foreach (StreamingChatMessageContent message in this._chat.InvokeStreamingAsync(cancellationToken).ConfigureAwait(false))
        {
            if (agent.Mode == AggregatorMode.Flat)
            {
                yield return message;
            }
        }

        ChatMessageContent[] history = await this._chat.GetChatMessagesAsync(cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
        if (history.Length > initialCount)
        {
            if (agent.Mode == AggregatorMode.Flat)
            {
                for (int index = history.Length - 1; index >= initialCount; --index)
                {
                    messages.Add(history[index]);
                }
            }
            else if (agent.Mode == AggregatorMode.Nested)
            {
                ChatMessageContent finalMessage = history[0]; // Order descending
                yield return new StreamingChatMessageContent(finalMessage.Role, finalMessage.Content) { AuthorName = finalMessage.AuthorName };
                messages.Add(finalMessage);
            }
        }
    }

    /// <inheritdoc/>
    protected internal override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Always receive the initial history from the owning chat.
        this._chat.AddChatMessages([.. history]);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected internal override Task ResetAsync(CancellationToken cancellationToken = default) =>
        this._chat.ResetAsync(cancellationToken);

    protected internal override string Serialize() =>
        JsonSerializer.Serialize(this._chat.Serialize());
}
