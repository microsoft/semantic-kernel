// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCreateCollectionSchemaRequest(WeaviateCollectionSchema collectionSchema)
{
    private const string ApiRoute = "schema";

    [JsonPropertyName("class")]
    public string? CollectionName { get; set; } = collectionSchema.CollectionName;

    [JsonPropertyName("vectorConfig")]
    public Dictionary<string, WeaviateCollectionSchemaVectorConfig> VectorConfigurations { get; set; } = collectionSchema.VectorConfigurations;

    [JsonPropertyName("properties")]
    public List<WeaviateCollectionSchemaProperty> Properties { get; set; } = collectionSchema.Properties;

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
