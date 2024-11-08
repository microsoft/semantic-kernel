// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which truncates chat history to the provide truncated size.
/// </summary>
/// <remarks>
/// The truncation process is triggered when the list length is great than the truncated size.
/// </remarks>
public sealed class TruncatingChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _truncatedSize;

    /// <summary>
    /// Creates a new instance of <see cref="TruncatingChatHistoryReducer"/>.
    /// </summary>
    /// <param name="truncatedSize">The size of the chat history after truncation.</param>
    public TruncatingChatHistoryReducer(int truncatedSize)
    {
        if (truncatedSize <= 0)
        {
            throw new ArgumentException("Truncated size must be greater than zero.", nameof(truncatedSize));
        }

        this._truncatedSize = truncatedSize;
    }

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.GetSystemMessage();
        var truncationIndex = ComputeTruncationIndex(chatHistory, this._truncatedSize, systemMessage is not null);

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
    private static int ComputeTruncationIndex(ChatHistory chatHistory, int truncatedSize, bool hasSystemMessage)
    {
        truncatedSize -= hasSystemMessage ? 1 : 0;
        if (chatHistory.Count <= truncatedSize)
        {
            return -1;
        }

        // Compute the index of truncation target
        var truncationIndex = chatHistory.Count - truncatedSize;

        // Skip function related content
        while (truncationIndex < chatHistory.Count)
        {
            if (chatHistory[truncationIndex].Items.Any(i => i is FunctionCallContent or FunctionResultContent))
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
