// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateUpsertCollectionObjectRequest(
    string collectionName,
    Guid id,
    JsonNode collectionObject)
{
    private const string ApiRoute = "objects";

    [JsonIgnore]
    public string CollectionName { get; set; } = collectionName;

    [JsonIgnore]
    public Guid Id { get; set; } = id;

    [JsonIgnore]
    public JsonNode CollectionObject { get; set; } = collectionObject;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePutRequest($"{ApiRoute}/{this.CollectionName}/{this.Id}", this.CollectionObject);
    }
}
