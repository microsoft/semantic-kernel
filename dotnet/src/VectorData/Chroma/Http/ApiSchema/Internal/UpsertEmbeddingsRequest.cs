﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Chroma;

internal sealed class UpsertEmbeddingsRequest
{
    [JsonIgnore]
    public string CollectionId { get; set; }

    [JsonPropertyName("ids")]
    public string[] Ids { get; set; }

    [JsonPropertyName("embeddings")]
    public ReadOnlyMemory<float>[] Embeddings { get; set; }

    [JsonPropertyName("metadatas")]
    public object[]? Metadatas { get; set; }

    public static UpsertEmbeddingsRequest Create(string collectionId, string[] ids, ReadOnlyMemory<float>[] embeddings, object[]? metadatas = null)
    {
        return new UpsertEmbeddingsRequest(collectionId, ids, embeddings, metadatas);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest($"collections/{this.CollectionId}/upsert", this);
    }

    #region private ================================================================================

    private UpsertEmbeddingsRequest(string collectionId, string[] ids, ReadOnlyMemory<float>[] embeddings, object[]? metadatas = null)
    {
        this.CollectionId = collectionId;
        this.Ids = ids;
        this.Embeddings = embeddings;
        this.Metadatas = metadatas;
    }

    #endregion
}
