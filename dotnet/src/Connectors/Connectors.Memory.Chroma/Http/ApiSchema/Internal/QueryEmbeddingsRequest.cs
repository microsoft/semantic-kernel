// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema.Internal;

internal sealed class QueryEmbeddingsRequest
{
    [JsonIgnore]
    public string CollectionId { get; set; }

    [JsonPropertyName("query_embeddings")]
    public ReadOnlyMemory<float>[] QueryEmbeddings { get; set; }

    [JsonPropertyName("n_results")]
    public int NResults { get; set; }

    [JsonPropertyName("include")]
    public string[]? Include { get; set; }

    public static QueryEmbeddingsRequest Create(string collectionId, ReadOnlyMemory<float>[] queryEmbeddings, int nResults, string[]? include = null)
    {
        return new QueryEmbeddingsRequest(collectionId, queryEmbeddings, nResults, include);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest($"collections/{this.CollectionId}/query", this);
    }

    #region private ================================================================================

    private QueryEmbeddingsRequest(string collectionId, ReadOnlyMemory<float>[] queryEmbeddings, int nResults, string[]? include = null)
    {
        this.CollectionId = collectionId;
        this.QueryEmbeddings = queryEmbeddings;
        this.NResults = nResults;
        this.Include = include;
    }

    #endregion
}
