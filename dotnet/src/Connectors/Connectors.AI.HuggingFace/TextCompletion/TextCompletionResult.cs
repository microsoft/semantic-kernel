// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

internal sealed class TextCompletionResult : ITextResult, ITextStreamingResult
{
    private readonly ModelResult _responseData;

    public TextCompletionResult(TextCompletionResponse responseData)
    {
        this._responseData = new ModelResult(responseData);
    }

    public ModelResult ModelResult => this._responseData;

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._responseData.GetResult<TextCompletionResponse>().Text ?? string.Empty);
    }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    async IAsyncEnumerable<string> ITextStreamingResult.GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken)
#pragma warning restore CS1998
    {
        yield return this._responseData.GetResult<TextCompletionResponse>().Text ?? string.Empty;
    }
}
