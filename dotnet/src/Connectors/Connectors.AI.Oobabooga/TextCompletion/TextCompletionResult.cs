// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="ITextResult"/>. Actual response object is stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
[Obsolete("This functionality is available as part of new NuGet package: https://www.nuget.org/packages/MyIA.SemanticKernel.Connectors.AI.Oobabooga/. This will be removed in a future release.")]
internal sealed class TextCompletionResult : ITextResult
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
