// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Instance of <see cref="IChatCompletionService"/> which will invoke a delegate
/// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
/// </summary>
public sealed class ChatCompletionServiceWithReducer(IChatCompletionService service, IChatHistoryReducer reducer) : IChatCompletionService
{
    private static IReadOnlyDictionary<string, object?> EmptyAttributes { get; } = new Dictionary<string, object?>();

    public IReadOnlyDictionary<string, object?> Attributes => EmptyAttributes;

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var reducedMessages = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
        var reducedHistory = reducedMessages is null ? chatHistory : new ChatHistory(reducedMessages);

        return await service.GetChatMessageContentsAsync(reducedHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var reducedMessages = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
        var history = reducedMessages is null ? chatHistory : new ChatHistory(reducedMessages);

        var messages = service.GetStreamingChatMessageContentsAsync(history, executionSettings, kernel, cancellationToken);
        await foreach (var message in messages)
        {
            yield return message;
        }
    }
}
