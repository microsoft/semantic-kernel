// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace AgentWithHistoryTruncation;

internal abstract class TruncationStrategy
{
    public abstract bool RequiresTruncation(ChatHistory history);

    // Must be async for summarization case
    public abstract IAsyncEnumerable<ChatMessageContent> TruncateAsync(ChatHistory history, CancellationToken cancellationToken);
}
