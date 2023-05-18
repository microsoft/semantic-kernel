// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatCompletionAsTextResult : ITextCompletionStreamingResult
{
    private readonly Func<CancellationToken, IAsyncEnumerable<string>> _getCompletionStreamingAsyncImpl;
    private readonly Func<CancellationToken, Task<string>> _getCompletionAsyncImpl;

    public ChatCompletionAsTextResult(
        Func<CancellationToken, IAsyncEnumerable<string>> getCompletionStreamingAsyncImpl,
        Func<CancellationToken, Task<string>> getCompletionAsyncImpl)
    {
        this._getCompletionStreamingAsyncImpl = getCompletionStreamingAsyncImpl;
        this._getCompletionAsyncImpl = getCompletionAsyncImpl;
    }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
        => this._getCompletionAsyncImpl(cancellationToken);

    public IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default)
        => this._getCompletionStreamingAsyncImpl(cancellationToken);
}
