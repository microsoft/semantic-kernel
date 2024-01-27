// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a base class for text generation service using GoogleVertex AI Gemini API.
/// </summary>
[EditorBrowsable(EditorBrowsableState.Never)]
[Browsable(false)]
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
