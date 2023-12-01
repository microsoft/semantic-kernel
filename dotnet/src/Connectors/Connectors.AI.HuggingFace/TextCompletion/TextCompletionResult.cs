// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

internal sealed class TextCompletionResult : ITextResult
{
    public TextCompletionResult(TextCompletionResponse responseData) =>
        this.ModelResult = new ModelResult(responseData);

    public ModelResult ModelResult { get; }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult(this.ModelResult.GetResult<TextCompletionResponse>().Text ?? string.Empty);
}
