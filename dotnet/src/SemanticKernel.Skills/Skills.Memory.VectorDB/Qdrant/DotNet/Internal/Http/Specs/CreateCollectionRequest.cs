// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using Qdrant.DotNet.Internal.Diagnostics;

namespace Qdrant.DotNet.Internal.Http.Specs;

internal class CreateCollectionRequest : IValidatable
{
    public static CreateCollectionRequest Create(string collectionName)
    {
        return new CreateCollectionRequest(collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        this.Settings.Validate();
    }

    public CreateCollectionRequest WithVectorSize(int size)
    {
        this.Settings.Size = size;
        return this;
    }

    public CreateCollectionRequest WithDistanceType(VectorDistanceType distanceType)
    {
        this.Settings.DistanceType = distanceType;
        return this;
    }

    public HttpRequestMessage Build()
    {
        this.Validate();

        return HttpRequest.CreatePutRequest(
            $"collections/{this._collectionName}?wait=true",
            payload: this);
    }

    #region private ================================================================================

    private readonly string _collectionName;

    [JsonPropertyName("vectors")]
    private VectorSettings Settings { get; set; }

    private CreateCollectionRequest(string collectionName)
    {
        this._collectionName = collectionName;
        this.Settings = new VectorSettings();
    }

    private class VectorSettings : IValidatable
    {
        [JsonPropertyName("size")]
        internal int Size { get; set; }

        [JsonPropertyName("distance")]
        internal string DistanceAsString
        {
            get { return DistanceTypeToString(this.DistanceType); }
        }

        [JsonIgnore]
        internal VectorDistanceType DistanceType { get; set; }

        public void Validate()
        {
            Verify.True(this.Size > 0, "The vector size must be greater than zero");
            Verify.NotNull(this.DistanceType, "The distance type has not been defined");
            Verify.True(this.DistanceType is VectorDistanceType.Cosine or VectorDistanceType.DotProduct or VectorDistanceType.Euclidean or VectorDistanceType.Manhattan,
                $"Distance type {this.DistanceType:G} not supported.");
        }

        private static string DistanceTypeToString(VectorDistanceType x)
        {
            return x switch
            {
                VectorDistanceType.Cosine => "Cosine",
                VectorDistanceType.DotProduct => "DotProduct",
                VectorDistanceType.Euclidean => "Euclidean",
                VectorDistanceType.Manhattan => "Manhattan",
                _ => throw new NotSupportedException($"Distance type {Enum.GetName(typeof(VectorDistanceType), x)} not supported")
            };
        }
    }

    #endregion
}
