// Copyright (c) Microsoft. All rights reserved.
using System;
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
    private readonly Func<IReadOnlyList<ChatMessageContent>, ChatMessageContent?>? _messageSelector = null;

    public AggregatorChannel(AgentChat chat, Func<IReadOnlyList<ChatMessageContent>, ChatMessageContent?>? messageSelector)
        : this(chat)
    {
        this._messageSelector = messageSelector;
    }

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken = default)
    {
        return this._chat.GetChatMessagesAsync(cancellationToken);
    }

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(AggregatorAgent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        List<ChatMessageContent>? messages = agent.Mode == AggregatorMode.Custom ? [] : null;
        ChatMessageContent? lastMessage = null;

        await foreach (ChatMessageContent message in this._chat.InvokeAsync(cancellationToken).ConfigureAwait(false))
        {
            // For AggregatorMode.Flat, the entire aggregated chat is merged into the owning chat.
            if (agent.Mode == AggregatorMode.Flat)
            {
                yield return (IsVisible: true, message);
            }

            messages?.Add(message);

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

        if (agent.Mode == AggregatorMode.Custom)
        {
            ChatMessageContent? selected = this.SelectMessage(messages!);
            if (selected is not null)
            {
                yield return (IsVisible: true, selected);
            }
        }
    }

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(AggregatorAgent agent, IList<ChatMessageContent> messages, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        int initialCount = 0;
        await foreach (var _ in this._chat.GetChatMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            initialCount++;
        }

        await foreach (StreamingChatMessageContent message in this._chat.InvokeStreamingAsync(cancellationToken).ConfigureAwait(false))
        {
            if (agent.Mode == AggregatorMode.Flat)
            {
                yield return message;
            }
        }

        List<ChatMessageContent> history = [];
        await foreach (var item in this._chat.GetChatMessagesAsync(cancellationToken).ConfigureAwait(false))
        {
            history.Add(item);
        }

        if (history.Count > initialCount)
        {
            if (agent.Mode == AggregatorMode.Flat)
            {
                for (int index = history.Count - 1; index >= initialCount; --index)
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
            else if (agent.Mode == AggregatorMode.Custom)
            {
                IReadOnlyList<ChatMessageContent> generatedMessages = history.Take(history.Count - initialCount).ToList();
                ChatMessageContent? selected = this.SelectMessage(generatedMessages);
                if (selected is not null)
                {
                    yield return new StreamingChatMessageContent(selected.Role, selected.Content) { AuthorName = selected.AuthorName };
                    messages.Add(selected);
                }
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

    private ChatMessageContent? SelectMessage(IReadOnlyList<ChatMessageContent> messages)
    {
        if (this._messageSelector is null)
        {
            throw new InvalidOperationException(
                $"{nameof(AggregatorAgent.MessageSelector)} must be configured when {nameof(AggregatorAgent.Mode)} is {AggregatorMode.Custom}.");
        }

        return this._messageSelector(messages);
    }
}
