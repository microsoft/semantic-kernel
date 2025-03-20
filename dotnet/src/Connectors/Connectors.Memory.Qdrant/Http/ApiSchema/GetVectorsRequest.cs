// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class GetVectorsRequest
{
    /// <summary>
    /// Name of the collection to request vectors from
    /// </summary>
    [JsonIgnore]
    public string Collection { get; set; }

    /// <summary>
    /// Read consistency guarantees for the operation
    /// </summary>
    [JsonPropertyName("consistency")]
    public int Consistency { get; set; } = 1;

    /// <summary>
    /// Array of vector IDs to retrieve
    /// </summary>
    [JsonPropertyName("ids")]
    public IEnumerable<string> PointIds { get; set; } = [];

    /// <summary>
    /// Select which payload to return with the response. Default: All
    /// </summary>
    [JsonPropertyName("with_payload")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? WithPayload { get; set; }

    /// <summary>
    /// Options for specifying which vector to include
    /// true - return all vector
    /// false - do not return vector
    /// </summary>
    [JsonPropertyName("with_vector")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? WithVector { get; set; }

    public static GetVectorsRequest Create(string collectionName)
    {
        return new GetVectorsRequest(collectionName);
    }

    public GetVectorsRequest WithPointId(string pointId)
    {
#if NET462
        var points = this.PointIds.ToList();
        points.Add(pointId);
        this.PointIds = points;
#else
        this.PointIds = this.PointIds.Append(pointId);
#endif
        return this;
    }

    public GetVectorsRequest WithPointIDs(IEnumerable<string> pointIds)
    {
        this.PointIds = pointIds;
        return this;
    }

    public GetVectorsRequest WithPayloads(bool withPayloads)
    {
        this.WithPayload = withPayloads;
        return this;
    }

    public GetVectorsRequest WithVectors(bool withEmbeddings)
    {
        this.WithVector = withEmbeddings;
        return this;
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(
            $"collections/{this.Collection}/points",
            payload: this);
    }

    #region private ================================================================================

    private GetVectorsRequest(string collectionName)
    {
        this.Collection = collectionName;
    }

    #endregion
}
