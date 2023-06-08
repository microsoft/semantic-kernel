// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

internal sealed class TextCompletionResult : ITextCompletionResult
{
    private readonly ModelResult _responseData;

    public TextCompletionResult(TextCompletionResponseText responseData)
    {
        this._responseData = new ModelResult(responseData);
    }

    public ModelResult ModelResult => this._responseData;

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._responseData.GetResult<TextCompletionResponseText>().Text ?? string.Empty);
    }
}
