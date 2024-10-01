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
    /// <param name="messageCount">Number of messages to include in the chat history</param>
    public static IChatCompletionService WithTrimmingChatHistoryReducer(this IChatCompletionService service, int messageCount)
    {
        return new ChatCompletionServiceWithReducer(service, new TrimmingChatHistoryReducer(messageCount));
    }

    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="maxTokenCount">Maximum number of tokens to be used by <see cref="ChatHistory"/></param>
    public static IChatCompletionService WithMaxTokensChatHistoryReducer(this IChatCompletionService service, int maxTokenCount)
    {
        return new ChatCompletionServiceWithReducer(service, new MaxTokensChatHistoryReducer(maxTokenCount));
    }

    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="messageCount">Number of messages to include in the chat history</param>
    public static IChatCompletionService WithSummarizingChatHistoryReducer(this IChatCompletionService service, int messageCount)
    {
        return new ChatCompletionServiceWithReducer(service, new SummarizingChatHistoryReducer(messageCount));
    }

    /// <summary>
    /// Returns the system prompt from the chat history.
    /// </summary>
    internal static ChatMessageContent? GetSystemMessage(this ChatHistory chatHistory)
    {
        return chatHistory.FirstOrDefault(m => m.Role == AuthorRole.System);
    }
}

internal class TrimmingChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _messageCount;

    internal TrimmingChatHistoryReducer(int messageCount)
    {
        this._messageCount = messageCount;
    }

    /// <inheritdoc/>
    public Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var systemMessage = chatHistory.GetSystemMessage();
        ChatHistory reducedChatHistory = systemMessage is not null ? new(systemMessage.Content!) : new();
        // trimming to just the last N messages
        reducedChatHistory.Add(chatHistory[^this._messageCount]);
        return Task.FromResult<ChatHistory>(reducedChatHistory);
    }
}

internal class MaxTokensChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _maxTokenCount;

    internal MaxTokensChatHistoryReducer(int maxTokenCount)
    {
        this._maxTokenCount = maxTokenCount;
    }

    /// <inheritdoc/>
    public Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        ChatHistory reducedChatHistory = [];
        var totalTokenCount = 0;
        var insertIndex = 0;
        var systemMessage = chatHistory.GetSystemMessage();
        if (systemMessage is not null)
        {
            reducedChatHistory.Add(systemMessage);
            totalTokenCount += (int)(systemMessage.Metadata?["TokenCount"] ?? 0);
            insertIndex = 1;
        }
        // Add the remaining messages that fit within the token limit
        for (int i = chatHistory.Count - 1; i >= 1; i--)
        {
            var tokenCount = (int)(chatHistory[i].Metadata?["TokenCount"] ?? 0);
            if (tokenCount + totalTokenCount > this._maxTokenCount)
            {
                break;
            }
            reducedChatHistory.Insert(insertIndex, chatHistory[i]);
            totalTokenCount += tokenCount;
        }
        return Task.FromResult<ChatHistory>(reducedChatHistory);
    }
}

internal class SummarizingChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _messageCount;

    internal SummarizingChatHistoryReducer(int messageCount)
    {
        this._messageCount = messageCount;
    }

    /// <inheritdoc/>
    public Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var systemMessage = chatHistory.GetSystemMessage();
        ChatHistory reducedChatHistory = systemMessage is not null ? new(systemMessage.Content!) : new();
        // add logic to summarize the chat history
        // adding the last N messages
        reducedChatHistory.Add(chatHistory[^this._messageCount]);
        return Task.FromResult<ChatHistory>(reducedChatHistory);
    }
}

/// <summary>
/// Interface for reducing the chat history before sending it to the chat completion provider.
/// </summary>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Reduce the <see cref="ChatHistory"/> before sending it to the <see cref="IChatCompletionService"/>.
    /// </summary>
    /// <param name="chatHistory">Instance of <see cref="ChatHistory"/>to be reduced.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken);
}

/// <summary>
/// Instance of <see cref="IChatCompletionService"/> which will invoke a delegate
/// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
/// </summary>
internal sealed class ChatCompletionServiceWithReducer(IChatCompletionService service, IChatHistoryReducer reducer) : IChatCompletionService
{
    public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        return await service.GetChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        var messages = service.GetStreamingChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken);
        await foreach (var message in messages)
        {
            yield return message;
        }
    }

}
