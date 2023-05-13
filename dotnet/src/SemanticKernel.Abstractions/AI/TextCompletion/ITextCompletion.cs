// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Interface for text completion services
/// </summary>
public interface ITextCompletion
{
    public Task<IReadOnlyList<ITextCompletionResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default);

    public IAsyncEnumerable<ITextCompletionStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default);
}
