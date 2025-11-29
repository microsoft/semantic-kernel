// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.VoyageAI.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI;

/// <summary>
/// VoyageAI multimodal embedding generation service.
/// Generates embeddings for text, images, or interleaved text and images.
/// Supports the voyage-multimodal-3 model.
/// </summary>
/// <remarks>
/// Constraints:
/// - Maximum 1,000 inputs per request
/// - Images: ≤16 million pixels, ≤20 MB
/// - Total tokens per input: ≤32,000 (560 pixels = 1 token)
/// - Aggregate tokens across inputs: ≤320,000
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VoyageAIMultimodalEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly VoyageAIClient _client;
    private readonly string _modelId;
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="VoyageAIMultimodalEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The VoyageAI model ID (e.g., voyage-multimodal-3).</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint (defaults to https://api.voyageai.com/v1).</param>
    /// <param name="httpClient">Optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory.</param>
    public VoyageAIMultimodalEmbeddingGenerationService(
        string modelId,
        string apiKey,
        string? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._modelId = modelId;
        this._client = new VoyageAIClient(
            apiKey,
            endpoint,
            httpClient,
            loggerFactory?.CreateLogger(typeof(VoyageAIMultimodalEmbeddingGenerationService)));

        this._attributes.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Generates multimodal embeddings for text and/or images.
    /// </summary>
    /// <param name="inputs">List of inputs. Each input can be:
    /// - A string (text)
    /// - A base64-encoded image string
    /// - A dictionary with "type" and "content" keys for mixed inputs</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>A list of multimodal embeddings.</returns>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateMultimodalEmbeddingsAsync(
        IList<object> inputs,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var request = new MultimodalEmbeddingRequest
        {
            Inputs = inputs,
            Model = this._modelId,
            InputType = null,
            Truncation = true
        };

        var response = await this._client.SendRequestAsync<MultimodalEmbeddingResponse>(
            "multimodalembeddings",
            request,
            cancellationToken).ConfigureAwait(false);

        var embeddings = response.Data
            .OrderBy(d => d.Index)
            .Select(d => new ReadOnlyMemory<float>(d.Embedding))
            .ToList();

        return embeddings;
    }

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Convert text-only inputs to multimodal format
        var inputs = data.Cast<object>().ToList();
        return await this.GenerateMultimodalEmbeddingsAsync(inputs, kernel, cancellationToken).ConfigureAwait(false);
    }
}
