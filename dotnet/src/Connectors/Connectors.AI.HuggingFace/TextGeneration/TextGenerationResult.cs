// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextGeneration;

internal sealed class TextGenerationResult : ITextResult
{
    public TextGenerationResult(TextGenerationResponse responseData) =>
        this.ModelResult = new ModelResult(responseData);

    public ModelResult ModelResult { get; }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult(this.ModelResult.GetResult<TextGenerationResponse>().Text ?? string.Empty);
}
