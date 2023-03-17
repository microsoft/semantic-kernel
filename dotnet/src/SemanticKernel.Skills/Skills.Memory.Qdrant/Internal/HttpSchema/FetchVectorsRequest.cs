// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class FetchVectorsRequest : IValidatable
{
    [JsonPropertyName("limit")]
    private int Limit { get; set; }

    [JsonPropertyName("offset")]
    private int Offset { get; set; }

    [JsonPropertyName("with_payload")]
    private bool WithPayload { get; set; }

    [JsonPropertyName("with_vector")]
    private bool WithVector { get; set; }

    [JsonPropertyName("filter")]
    private Filter Filters { get; set; }

    public static FetchVectorsRequest Fetch(string collectionName)
    {
        return new FetchVectorsRequest(collectionName);
    }

    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        this.Filters.Validate();
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/scroll");
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private FetchVectorsRequest(string collectionName)
    {
        this._collectionName = collectionName;
        this.Filters = new Filter();
        this.WithPayload = true;
        this.WithVector = true;
    }

    #endregion
}
