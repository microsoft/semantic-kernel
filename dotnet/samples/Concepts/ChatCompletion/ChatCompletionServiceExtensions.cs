// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Extensions methods for <see cref="IChatCompletionService"/>
/// </summary>
internal static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="reducer">Instances of <see cref="ChatHistoryReducer"/></param>
    public static IChatCompletionService WithChatHistoryReducer(this IChatCompletionService service, ChatHistoryReducer reducer)
    {
        return new ChatCompletionServiceWithReducer(service, reducer);
    }
}

/// <summary>
/// Delegate for reducing the chat history before sending it to the chat completion provider.
/// </summary>
internal delegate Task<ChatHistory?> ChatHistoryReducer(ChatHistory chatHistory, CancellationToken cancellationToken);

/// <summary>
/// Instance of <see cref="IChatCompletionService"/> which will invoke a delegate
/// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
/// </summary>
internal sealed class ChatCompletionServiceWithReducer(IChatCompletionService service, ChatHistoryReducer reducer) : IChatCompletionService
{
    public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer(chatHistory, cancellationToken).ConfigureAwait(false);

        return await service.GetChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer(chatHistory, cancellationToken).ConfigureAwait(false);

        var messages = service.GetStreamingChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken);
        await foreach (var message in messages)
        {
            yield return message;
        }
    }
}
