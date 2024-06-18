// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text embedding service.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly OpenAIClientCore _core;
    private readonly int? _dimensions;

    /// <summary>
    /// Create an instance of the OpenAI text embedding connector
    /// </summary>
    /// <param name="options">Options for the Text Embedding Service.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public OpenAITextEmbeddingGenerationService(
        OpenAIClientTextEmbeddingGenerationOptions options,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(options.ModelId);

        this._core = new(
            modelId: options.ModelId,
            apiKey: options.ApiKey,
            organization: options.OrganizationId,
            httpClient: httpClient,
            logger: options.LoggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGenerationService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, options.ModelId);

        this._dimensions = options.Dimensions;
    }

    /// <summary>
    /// Create an instance of the OpenAI text embedding connector
    /// </summary>
    /// <param name="options">Options for the Text Embedding Service.</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    public OpenAITextEmbeddingGenerationService(
        OpenAITextEmbeddingGenerationOptions options,
        OpenAIClient openAIClient)
    {
        Verify.NotNull(options.ModelId);

        this._core = new(options.ModelId, openAIClient, options.LoggerFactory?.CreateLogger(typeof(OpenAITextEmbeddingGenerationService)));
        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, options.ModelId);

        this._dimensions = options.Dimensions;
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._core.LogActionDetails();
        return this._core.GetEmbeddingsAsync(data, kernel, this._dimensions, cancellationToken);
    }
}
