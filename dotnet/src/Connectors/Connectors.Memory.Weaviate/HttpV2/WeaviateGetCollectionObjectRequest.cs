// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateGetCollectionObjectRequest(string collectionName, Guid id)
{
    private const string ApiRoute = "schema";

    [JsonIgnore]
    public string CollectionName { get; set; } = collectionName;

    [JsonIgnore]
    public Guid Id { get; set; } = id;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreateGetRequest($"{ApiRoute}/{this.CollectionName}/{this.Id}");
    }
}
