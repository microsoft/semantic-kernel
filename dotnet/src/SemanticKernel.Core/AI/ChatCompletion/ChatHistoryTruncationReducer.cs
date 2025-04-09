// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Truncate the chat history to the target message count.
/// </summary>
/// <remarks>
/// Truncation will always avoid orphaning function-content as the presence of
/// a function-call _must_ be followed by a function-result.  When a threshold count is
/// is provided (recommended), reduction will scan within the threshold window in an attempt to
/// avoid orphaning a user message from an assistant response.
/// </remarks>
public class ChatHistoryTruncationReducer : IChatHistoryReducer
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryTruncationReducer"/> class.
    /// </summary>
    /// <param name="targetCount">The desired number of target messages after reduction.</param>
    /// <param name="thresholdCount">An optional number of messages beyond the 'targetCount' that must be present in order to trigger reduction/</param>
    /// <remarks>
    /// While the 'thresholdCount' is optional, it is recommended to provided so that reduction is not triggered
    /// for every incremental addition to the chat history beyond the 'targetCount'.
    /// </remarks>>
    public ChatHistoryTruncationReducer(int targetCount, int? thresholdCount = null)
    {
        Verify.True(targetCount > 0, "Target message count must be greater than zero.");
        Verify.True(!thresholdCount.HasValue || thresholdCount > 0, "The reduction threshold length must be greater than zero.");

        this._targetCount = targetCount;

        this._thresholdCount = thresholdCount ?? 0;
    }

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.FirstOrDefault(l => l.Role == AuthorRole.System);

        // First pass to determine the truncation index
        int truncationIndex = chatHistory.LocateSafeReductionIndex(this._targetCount, this._thresholdCount, hasSystemMessage: systemMessage is not null);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            // Second pass to truncate the history
            truncatedHistory = chatHistory.Extract(truncationIndex, systemMessage: systemMessage);
        }

        return Task.FromResult(truncatedHistory);
    }

    /// <inheritdoc/>
    public override bool Equals(object? obj)
    {
        ChatHistoryTruncationReducer? other = obj as ChatHistoryTruncationReducer;
        return other != null &&
               this._thresholdCount == other._thresholdCount &&
               this._targetCount == other._targetCount;
    }

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(nameof(ChatHistoryTruncationReducer), this._thresholdCount, this._targetCount);

    private readonly int _thresholdCount;
    private readonly int _targetCount;
}
