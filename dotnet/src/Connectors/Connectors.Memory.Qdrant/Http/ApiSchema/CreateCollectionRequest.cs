// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class CreateCollectionRequest
{
    /// <summary>
    /// The name of the collection to create
    /// </summary>
    [JsonIgnore]
    public string CollectionName { get; set; }

    /// <summary>
    /// Collection settings consisting of a common vector length and vector distance calculation standard
    /// </summary>
    [JsonPropertyName("vectors")]
    public VectorSettings Settings { get; set; }

    public static CreateCollectionRequest Create(string collectionName, int vectorSize, QdrantDistanceType distanceType)
    {
        return new CreateCollectionRequest(collectionName, vectorSize, distanceType);
    }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePutRequest(
            $"collections/{this.CollectionName}?wait=true",
            payload: this);
    }

    internal sealed class VectorSettings(int vectorSize, QdrantDistanceType distanceType)
    {
        [JsonPropertyName("size")]
        public int? Size { get; set; } = vectorSize;

        [JsonPropertyName("distance")]
        public string? DistanceAsString
        {
            get { return DistanceTypeToString(this.DistanceType); }
        }

        [JsonIgnore]
        private QdrantDistanceType DistanceType { get; set; } = distanceType;

        private static string DistanceTypeToString(QdrantDistanceType x)
        {
            return x switch
            {
                QdrantDistanceType.Cosine => "Cosine",
                QdrantDistanceType.DotProduct => "DotProduct",
                QdrantDistanceType.Euclidean => "Euclidean",
                QdrantDistanceType.Manhattan => "Manhattan",
                _ => throw new NotSupportedException($"Distance type {x} not supported")
            };
        }
    }

    #region private ================================================================================

    private CreateCollectionRequest(string collectionName, int vectorSize, QdrantDistanceType distanceType)
    {
        this.CollectionName = collectionName;
        this.Settings = new VectorSettings(vectorSize, distanceType);
    }

    #endregion
}
