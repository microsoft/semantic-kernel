// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.TextCompletion;

internal class TextCompletionStreamingResult : ITextCompletionStreamingResult
{
    private readonly string _result;

    public TextCompletionStreamingResult(string? result)
    {
        this._result = result ?? string.Empty;
    }

    public Task<string> CompleteAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._result);
    }

    public IAsyncEnumerable<string> CompleteStreamAsync(CancellationToken cancellationToken = default)
    {
        return this.CompleteAsync(cancellationToken).ToAsyncEnumerable();
    }
}
