// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace AgentWithHistoryTruncation;

internal class MessageCountTruncationStrategy(int truncationThreshold) : TruncationStrategy
{
    // Strict trigger will truncate often once threshold is reached.
    // Specifying a buffer / window beyond the threshold could reduce the frequency of truncation:
    // At x + y messages, truncate to x messages.
    public override bool RequiresTruncation(ChatHistory history) => history.Count >= truncationThreshold;

    public override IAsyncEnumerable<ChatMessageContent> TruncateAsync(ChatHistory history, CancellationToken cancellationToken)
    {
        return GetTruncatedHistory().ToAsyncEnumerable();

        IEnumerable<ChatMessageContent> GetTruncatedHistory()
        {
            for (int index = history.Count - truncationThreshold; index < history.Count - 1; ++index)
            {
                yield return history[index];
            }
        }
    }

    // Override so that different instances with the same threshold are considered equal.
    public override int GetHashCode() => HashCode.Combine(nameof(MessageCountTruncationStrategy), truncationThreshold);
}
