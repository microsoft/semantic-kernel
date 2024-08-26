// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateUpsertCollectionObjectBatchRequest(List<JsonNode> collectionObjects)
{
    private const string ApiRoute = "batch/objects";

    [JsonPropertyName("fields")]
    public List<string> Fields { get; set; } = [WeaviateConstants.ReservedKeyPropertyName];

    [JsonPropertyName("objects")]
    public List<JsonNode> CollectionObjects { get; set; } = collectionObjects;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
