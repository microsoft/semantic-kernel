// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// Truncate the chat history to the target message count.
/// </summary>
/// <remarks>
/// Truncation will always Will avoid orphaning function-content as  the presense of
/// a function-call _must_ be followed by a function-result.  When a threshold count is
/// is provided (recommended), truncation will scan within the threshold window in an attempt to
/// avoid orphaning a user message from an assistant response.
/// </remarks>
internal class ChatHistoryTruncationReducer : IChatHistoryReducer
{
    private readonly int _thresholdCount;
    private readonly int _targetCount;

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(nameof(ChatHistoryTruncationReducer), this._thresholdCount, this._targetCount);

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // First pass to determine the truncation index
        int truncationIndex = this.DetermineTruncationIndex(history);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            // Second pass to truncate the history
            truncatedHistory = this.TruncateHistory(history, truncationIndex);
        }

        return Task.FromResult(truncatedHistory);
    }

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

    private IEnumerable<ChatMessageContent> TruncateHistory(IReadOnlyList<ChatMessageContent> history, int truncationIndex)
    {
        for (int index = truncationIndex; index < history.Count; ++index)
        {
            yield return history[index];
        }
    }

    private int DetermineTruncationIndex(IReadOnlyList<ChatMessageContent> history)
    {
        // Compute the index of the trunction threshold
        int thresholdIndex = history.Count - this._thresholdCount - this._targetCount;

        if (thresholdIndex <= 0)
        {
            // History is too short to truncate
            return 0;
        }

        // Compute the index of truncation target
        int messageIndex = history.Count - this._targetCount;

        // Skip function related content
        while (messageIndex >= 0)
        {
            if (!history[messageIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                break;
            }

            --messageIndex;
        }

        // Capture the earliest non-function related message
        int targetIndex = messageIndex;

        // Scan for user message within truncation range to maximize chat cohesion
        while (messageIndex >= thresholdIndex)
        {
            // A user message provides a superb truncation point
            if (history[messageIndex].Role == AuthorRole.User)
            {
                return messageIndex;
            }

            --messageIndex;
        }

        // No user message found, fallback to the earliest non-function related message
        return targetIndex;
    }
}
