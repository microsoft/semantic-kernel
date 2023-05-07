// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

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

    internal sealed class VectorSettings : IValidatable
    {
        [JsonPropertyName("size")]
        public int? Size { get; set; }

        [JsonPropertyName("distance")]
        public string? DistanceAsString
        {
            get { return DistanceTypeToString(this.DistanceType); }
        }

        [JsonIgnore]
        private QdrantDistanceType DistanceType { get; set; }

        public void Validate()
        {
            Verify.True(this.Size > 0, "The vector size must be greater than zero");
            Verify.NotNull(this.DistanceType, "The distance type has not been defined");
            Verify.True(
                this.DistanceType is QdrantDistanceType.Cosine or QdrantDistanceType.DotProduct or QdrantDistanceType.Euclidean or QdrantDistanceType.Manhattan,
                $"Distance type {this.DistanceType:G} not supported.");
        }

        public VectorSettings(int vectorSize, QdrantDistanceType distanceType)
        {
            this.Size = vectorSize;
            this.DistanceType = distanceType;
        }

        private static string DistanceTypeToString(QdrantDistanceType x)
        {
            return x switch
            {
                QdrantDistanceType.Cosine => "Cosine",
                QdrantDistanceType.DotProduct => "DotProduct",
                QdrantDistanceType.Euclidean => "Euclidean",
                QdrantDistanceType.Manhattan => "Manhattan",
                _ => throw new NotSupportedException($"Distance type {Enum.GetName(typeof(QdrantDistanceType), x)} not supported")
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
