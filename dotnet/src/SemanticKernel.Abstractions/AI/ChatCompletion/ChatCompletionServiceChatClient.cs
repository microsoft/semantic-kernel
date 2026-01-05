// Copyright (c) Microsoft. All rights reserved.

#if !UNITY
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides an implementation of <see cref="IChatClient"/> around an arbitrary <see cref="IChatCompletionService"/>.</summary>
internal sealed class ChatCompletionServiceChatClient : IChatClient
{
    /// <summary>The wrapped <see cref="IChatCompletionService"/>.</summary>
    private readonly IChatCompletionService _chatCompletionService;

    /// <summary>Initializes the <see cref="ChatCompletionServiceChatClient"/> for <paramref name="chatCompletionService"/>.</summary>
    internal ChatCompletionServiceChatClient(IChatCompletionService chatCompletionService)
    {
        Verify.NotNull(chatCompletionService);

        this._chatCompletionService = chatCompletionService;

        this.Metadata = new ChatClientMetadata(
            chatCompletionService.GetType().Name,
            chatCompletionService.GetEndpoint() is string endpoint ? new Uri(endpoint) : null,
            chatCompletionService.GetModelId());
    }

    /// <inheritdoc />
    public ChatClientMetadata Metadata { get; }

    /// <inheritdoc />
    public async Task<Extensions.AI.ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        ChatHistory chatHistory = new(messages.Select(m => m.ToChatMessageContent()));
        int preCount = chatHistory.Count;

        var response = await this._chatCompletionService.GetChatMessageContentAsync(
            chatHistory,
            options.ToPromptExecutionSettings(),
            kernel: null,
            cancellationToken).ConfigureAwait(false);

        ChatResponse chatResponse = new()
        {
            ModelId = response.ModelId,
            RawRepresentation = response.InnerContent,
        };

        // Add all messages that were added to the history.
        // Then add the result message.
        for (int i = preCount; i < chatHistory.Count; i++)
        {
            chatResponse.Messages.Add(chatHistory[i].ToChatMessage());
        }

        chatResponse.Messages.Add(response.ToChatMessage());

        return chatResponse;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        await foreach (var update in this._chatCompletionService.GetStreamingChatMessageContentsAsync(
            new ChatHistory(messages.Select(m => m.ToChatMessageContent())),
            options.ToPromptExecutionSettings(),
            kernel: null,
            cancellationToken).ConfigureAwait(false))
        {
            yield return update.ToChatResponseUpdate();
        }
    }

    /// <inheritdoc />
    public void Dispose()
    {
        (this._chatCompletionService as IDisposable)?.Dispose();
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            serviceType.IsInstanceOfType(this._chatCompletionService) ? this._chatCompletionService :
            serviceType.IsInstanceOfType(this.Metadata) ? this.Metadata :
            null;
    }
}
#endif
