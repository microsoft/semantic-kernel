// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal sealed class CreateCollectionRequest : IValidatable
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

    public CreateCollectionRequest WithDistanceType(QdrantDistanceType distanceType)
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



    #endregion
}
