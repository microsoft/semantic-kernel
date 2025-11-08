// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.VoyageAI.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI;

/// <summary>
/// VoyageAI text embedding generation service.
/// Supports models like voyage-3-large, voyage-3.5, voyage-code-3, voyage-finance-2, voyage-law-2.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly VoyageAIClient _client;
    private readonly string _modelId;
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="VoyageAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The VoyageAI model ID.</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint (defaults to https://api.voyageai.com/v1).</param>
    /// <param name="httpClient">Optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory.</param>
    public VoyageAITextEmbeddingGenerationService(
        string modelId,
        string apiKey,
        string? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        ArgumentNullException.ThrowIfNullOrWhiteSpace(modelId);
        ArgumentNullException.ThrowIfNullOrWhiteSpace(apiKey);

        this._modelId = modelId;
        this._client = new VoyageAIClient(
            apiKey,
            endpoint,
            httpClient,
            loggerFactory?.CreateLogger(typeof(VoyageAITextEmbeddingGenerationService)));

        this._attributes.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var request = new EmbeddingRequest
        {
            Input = data,
            Model = this._modelId,
            InputType = null,
            Truncation = true,
            OutputDimension = null,
            OutputDtype = null
        };

        var response = await this._client.SendRequestAsync<EmbeddingResponse>(
            "embeddings",
            request,
            cancellationToken).ConfigureAwait(false);

        var embeddings = response.Data
            .OrderBy(d => d.Index)
            .Select(d => new ReadOnlyMemory<float>(d.Embedding))
            .ToList();

        return embeddings;
    }
}
