// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// %%%
/// </summary>
internal class ChatHistorySummarizationStrategy : IChatHistoryReducer
{
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public ChatHistorySummarizationStrategy(Kernel kernel, KernelFunction summarizerFunction, int maximumLength, int? targetLength = null)
    {
        throw new NotImplementedException();
    }
}
