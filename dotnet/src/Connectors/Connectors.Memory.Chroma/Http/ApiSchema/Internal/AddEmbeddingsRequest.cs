// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema.Internal;

internal sealed class AddEmbeddingsRequest
{
    [JsonIgnore]
    public string CollectionId { get; set; }

    [JsonPropertyName("ids")]
    public string[] Ids { get; set; }

    [JsonPropertyName("embeddings")]
    public float[][] Embeddings { get; set; }

    [JsonPropertyName("metadatas")]
    public object[]? Metadatas { get; set; }

    public static AddEmbeddingsRequest Create(string collectionId, string[] ids, float[][] embeddings, object[]? metadatas = null)
    {
        return new AddEmbeddingsRequest(collectionId, ids, embeddings, metadatas);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest($"collections/{this.CollectionId}/add", this);
    }

    #region private ================================================================================

    private AddEmbeddingsRequest(string collectionId, string[] ids, float[][] embeddings, object[]? metadatas = null)
    {
        this.CollectionId = collectionId;
        this.Ids = ids;
        this.Embeddings = embeddings;
        this.Metadatas = metadatas;
    }

    #endregion
}
