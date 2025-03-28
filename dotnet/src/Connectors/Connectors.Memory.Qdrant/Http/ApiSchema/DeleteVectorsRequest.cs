// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class DeleteVectorsRequest
{
    [JsonPropertyName("points")]
    public List<string> Ids { get; set; }

    public static DeleteVectorsRequest DeleteFrom(string collectionName)
    {
        return new DeleteVectorsRequest(collectionName);
    }

    public DeleteVectorsRequest DeleteVector(string qdrantPointId)
    {
        Verify.NotNull(qdrantPointId, "The point ID is NULL");
        this.Ids.Add(qdrantPointId);
        return this;
    }

    public DeleteVectorsRequest DeleteRange(IEnumerable<string> qdrantPointIds)
    {
        Verify.NotNull(qdrantPointIds, "The point ID collection is NULL");
        this.Ids.AddRange(qdrantPointIds);
        return this;
    }

    public HttpRequestMessage Build()
    {
        Verify.NotNullOrWhiteSpace(this._collectionName, "collectionName");
        Verify.NotNullOrEmpty(this.Ids, "The list of vectors to delete is NULL or empty");

        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/delete",
            payload: this);
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private DeleteVectorsRequest(string collectionName)
    {
        this.Ids = [];
        this._collectionName = collectionName;
    }

    #endregion
}
