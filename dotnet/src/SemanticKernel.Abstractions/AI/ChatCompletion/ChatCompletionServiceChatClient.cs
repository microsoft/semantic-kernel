// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
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
    public async Task<Extensions.AI.ChatResponse> GetResponseAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatMessages);

        var response = await this._chatCompletionService.GetChatMessageContentAsync(
            new ChatHistory(chatMessages.Select(m => m.ToChatMessageContent())),
            options.ToPromptExecutionSettings(),
            kernel: null,
            cancellationToken).ConfigureAwait(false);

        return new(response.ToChatMessage())
        {
            ModelId = response.ModelId,
            RawRepresentation = response.InnerContent,
        };
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chatMessages);

        await foreach (var update in this._chatCompletionService.GetStreamingChatMessageContentsAsync(
            new ChatHistory(chatMessages.Select(m => m.ToChatMessageContent())),
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
