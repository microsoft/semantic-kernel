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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonNode> collectionObjects)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonNode> collectionObjects)
=======
    public WeaviateUpsertCollectionObjectBatchRequest(List<JsonObject> collectionObjects)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    {
        this.CollectionObjects = collectionObjects;
    }

    [JsonPropertyName("fields")]
    public List<string> Fields { get; set; } = [WeaviateConstants.ReservedKeyPropertyName];

    [JsonPropertyName("objects")]
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public List<JsonNode>? CollectionObjects { get; set; }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public List<JsonNode>? CollectionObjects { get; set; }
=======
    public List<JsonObject>? CollectionObjects { get; set; }
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
