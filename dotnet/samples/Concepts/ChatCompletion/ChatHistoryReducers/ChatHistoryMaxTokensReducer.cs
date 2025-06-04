// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the specified max token count.
/// </summary>
/// <remarks>
/// This reducer requires that the ChatMessageContent.MetaData contains a TokenCount property.
/// </remarks>
public sealed class ChatHistoryMaxTokensReducer : IChatHistoryReducer
{
    private readonly int _maxTokenCount;

    /// <summary>
    /// Creates a new instance of <see cref="ChatHistoryMaxTokensReducer"/>.
    /// </summary>
    /// <param name="maxTokenCount">Max token count to send to the model.</param>
    public ChatHistoryMaxTokensReducer(int maxTokenCount)
    {
        if (maxTokenCount <= 0)
        {
            throw new ArgumentException("Maximum token count must be greater than zero.", nameof(maxTokenCount));
        }

        this._maxTokenCount = maxTokenCount;
    }

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.GetSystemMessage();

        var truncationIndex = ComputeTruncationIndex(chatHistory, systemMessage);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            truncatedHistory = chatHistory.Extract(truncationIndex, systemMessage: systemMessage);
        }

        return Task.FromResult<IEnumerable<ChatMessageContent>?>(truncatedHistory);
    }

    #region private

    /// <summary>
    /// Compute the index truncation where truncation should begin using the current truncation threshold.
    /// </summary>
    /// <param name="chatHistory">Chat history to be truncated.</param>
    /// <param name="systemMessage">The system message</param>
    private int ComputeTruncationIndex(IReadOnlyList<ChatMessageContent> chatHistory, ChatMessageContent? systemMessage)
    {
        var truncationIndex = -1;

        var totalTokenCount = (int)(systemMessage?.Metadata?["TokenCount"] ?? 0);
        for (int i = chatHistory.Count - 1; i >= 0; i--)
        {
            truncationIndex = i;
            var tokenCount = (int)(chatHistory[i].Metadata?["TokenCount"] ?? 0);
            if (tokenCount + totalTokenCount > this._maxTokenCount)
            {
                break;
            }
            totalTokenCount += tokenCount;
        }

        // Skip function related content
        while (truncationIndex < chatHistory.Count)
        {
            if (chatHistory[truncationIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                truncationIndex++;
            }
            else
            {
                break;
            }
        }

        return truncationIndex;
    }

    #endregion
}
