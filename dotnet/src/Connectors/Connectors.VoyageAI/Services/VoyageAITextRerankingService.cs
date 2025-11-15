// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.VoyageAI.Core;
using Microsoft.SemanticKernel.Reranking;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.VoyageAI;

/// <summary>
/// VoyageAI text reranking service.
/// Supports models like rerank-2.5, rerank-2.5-lite, rerank-2, rerank-2-lite, rerank-1.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VoyageAITextRerankingService : ITextRerankingService
{
    private readonly VoyageAIClient _client;
    private readonly string _modelId;
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="VoyageAITextRerankingService"/> class.
    /// </summary>
    /// <param name="modelId">The VoyageAI reranker model ID (e.g., rerank-2.5).</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint (defaults to https://api.voyageai.com/v1).</param>
    /// <param name="httpClient">Optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory.</param>
    public VoyageAITextRerankingService(
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
            loggerFactory?.CreateLogger(typeof(VoyageAITextRerankingService)));

        this._attributes.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public async Task<IList<RerankResult>> RerankAsync(
        string query,
        IList<string> documents,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var request = new RerankRequest
        {
            Query = query,
            Documents = documents,
            Model = this._modelId,
            TopK = null,
            Truncation = true
        };

        var response = await this._client.SendRequestAsync<RerankResponse>(
            "rerank",
            request,
            cancellationToken).ConfigureAwait(false);

        // Create a map from index to document for lookup
        var documentMap = documents.Select((doc, index) => new { index, doc })
            .ToDictionary(x => x.index, x => x.doc);

        var results = response.Data
            .Where(r => documentMap.ContainsKey(r.Index))  // Validate index exists
            .OrderByDescending(r => r.RelevanceScore)
            .Select(r => new RerankResult(r.Index, documentMap[r.Index], r.RelevanceScore))
            .ToList();

        return results;
    }
}
