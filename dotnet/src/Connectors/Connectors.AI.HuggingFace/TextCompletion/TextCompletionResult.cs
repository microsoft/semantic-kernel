// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

internal sealed class TextCompletionStreamingResult : ITextCompletionStreamingResult
{
    private readonly ModelResult _responseData;

    public TextCompletionStreamingResult(TextCompletionResponse responseData)
    {
        this._responseData = new ModelResult(responseData);
    }

    public ModelResult ModelResult => this._responseData;

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._responseData.GetResult<TextCompletionResponse>().Text ?? string.Empty);
    }

    public IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default)
    {
        return this.GetCompletionAsync(cancellationToken).ToAsyncEnumerable();
    }
}
