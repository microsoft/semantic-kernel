// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateGetCollectionObjectRequest(string collectionName, Guid id, bool includeVectors)
{
    private const string ApiRoute = "objects";
    private const string IncludeQueryParameterName = "include";
    private const string IncludeVectorQueryParameterValue = "vector";

    [JsonIgnore]
    public string CollectionName { get; set; } = collectionName;

    [JsonIgnore]
    public Guid Id { get; set; } = id;

    [JsonIgnore]
    public bool IncludeVectors { get; set; } = includeVectors;

    public HttpRequestMessage Build()
    {
        var uri = $"{ApiRoute}/{this.CollectionName}/{this.Id}";

        if (this.IncludeVectors)
        {
            uri += $"?{IncludeQueryParameterName}={IncludeVectorQueryParameterValue}";
        }

        return HttpRequest.CreateGetRequest(uri);
    }
}
