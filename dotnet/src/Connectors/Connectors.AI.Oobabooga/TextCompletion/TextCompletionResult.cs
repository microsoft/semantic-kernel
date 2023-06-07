// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

internal sealed class TextCompletionResult : ITextCompletionResult
{
    private readonly string _result;

    public TextCompletionResult(string result)
    {
        this._result = result ?? string.Empty;
    }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._result);
    }
}

internal sealed class TextCompletionStreamingResult : ITextCompletionStreamingResult
{
    private readonly string _result;

    public TextCompletionStreamingResult(string? result)
    {
        this._result = result ?? string.Empty;
    }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._result);
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        yield return await this.GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }
}
