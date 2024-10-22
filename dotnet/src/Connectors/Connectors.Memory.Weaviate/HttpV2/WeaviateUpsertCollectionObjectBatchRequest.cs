// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateUpsertCollectionObjectBatchRequest
{
    private const string ApiRoute = "batch/objects";

    [JsonConstructor]
    public WeaviateUpsertCollectionObjectBatchRequest() { }

    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonObject> collectionObjects)
    {
        this.CollectionObjects = collectionObjects;
    }

    [JsonPropertyName("fields")]
    public List<string> Fields { get; set; } = [WeaviateConstants.ReservedKeyPropertyName];

    [JsonPropertyName("objects")]
    public List<JsonObject>? CollectionObjects { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
