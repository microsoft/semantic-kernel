// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.VoyageAI.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI;

/// <summary>
/// VoyageAI contextualized embedding generation service.
/// Generates embeddings that capture both local chunk details and global document-level metadata.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAIContextualizedEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly VoyageAIClient _client;
    private readonly string _modelId;
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="VoyageAIContextualizedEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The VoyageAI model ID (e.g., voyage-3).</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint (defaults to https://api.voyageai.com/v1).</param>
    /// <param name="httpClient">Optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory.</param>
    public VoyageAIContextualizedEmbeddingGenerationService(
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
            loggerFactory?.CreateLogger(typeof(VoyageAIContextualizedEmbeddingGenerationService)));

        this._attributes.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Generates contextualized embeddings for document chunks.
    /// </summary>
    /// <param name="inputs">List of lists where each inner list contains document chunks.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>A list of embeddings for all chunks across all documents.</returns>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateContextualizedEmbeddingsAsync(
        IList<IList<string>> inputs,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var request = new ContextualizedEmbeddingRequest
        {
            Inputs = inputs,
            Model = this._modelId,
            InputType = null,
            Truncation = true
        };

        var response = await this._client.SendRequestAsync<ContextualizedEmbeddingResponse>(
            "contextualizedembeddings",
            request,
            cancellationToken).ConfigureAwait(false);

        var embeddings = new List<ReadOnlyMemory<float>>();
        foreach (var result in response.Results)
        {
            foreach (var item in result.Embeddings)
            {
                embeddings.Add(new ReadOnlyMemory<float>(item.Embedding));
            }
        }

        return embeddings;
    }

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // Wrap data as a single input for contextualized embeddings
        var inputs = new List<IList<string>> { data };
        return await this.GenerateContextualizedEmbeddingsAsync(inputs, kernel, cancellationToken).ConfigureAwait(false);
    }
}
