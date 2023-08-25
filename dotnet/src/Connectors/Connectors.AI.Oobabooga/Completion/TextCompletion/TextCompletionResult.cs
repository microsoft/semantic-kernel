// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="ITextResult"/>. Actual response object is stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
public sealed class TextCompletionResult : ITextResult
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
