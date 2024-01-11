#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

public abstract class GeminiTextGenerationServiceBase : ITextGenerationService
{
    private protected Dictionary<string, object?> AttributesInternal { get; } = new();
    private protected IGeminiTextGenerationClient TextGenerationClient { get; init; } = null!;

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.TextGenerationClient.GenerateTextAsync(prompt, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.TextGenerationClient.StreamGenerateTextAsync(prompt, executionSettings, cancellationToken);
    }
}
