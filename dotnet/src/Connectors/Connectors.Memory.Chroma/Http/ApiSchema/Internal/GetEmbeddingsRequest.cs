// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema.Internal;

internal sealed class GetEmbeddingsRequest
{
    [JsonIgnore]
    public string CollectionId { get; set; }

    [JsonPropertyName("ids")]
    public string[] Ids { get; set; }

    [JsonPropertyName("include")]
    public string[]? Include { get; set; }

    public static GetEmbeddingsRequest Create(string collectionId, string[] ids, string[]? include = null)
    {
        return new GetEmbeddingsRequest(collectionId, ids, include);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest($"collections/{this.CollectionId}/get", this);
    }

    #region private ================================================================================

    private GetEmbeddingsRequest(string collectionId, string[] ids, string[]? include = null)
    {
        this.CollectionId = collectionId;
        this.Ids = ids;
        this.Include = include;
    }

    #endregion
}
