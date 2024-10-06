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

<<<<<<< Updated upstream
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonNode> collectionObjects)
=======
<<<<<<< HEAD
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonNode> collectionObjects)
=======
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonObject> collectionObjects)
>>>>>>> main
>>>>>>> Stashed changes
    {
        this.CollectionObjects = collectionObjects;
    }

    [JsonPropertyName("fields")]
    public List<string> Fields { get; set; } = [WeaviateConstants.ReservedKeyPropertyName];

    [JsonPropertyName("objects")]
<<<<<<< Updated upstream
    public List<JsonNode>? CollectionObjects { get; set; }
=======
<<<<<<< HEAD
    public List<JsonNode>? CollectionObjects { get; set; }
=======
    public List<JsonObject>? CollectionObjects { get; set; }
>>>>>>> main
>>>>>>> Stashed changes

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
