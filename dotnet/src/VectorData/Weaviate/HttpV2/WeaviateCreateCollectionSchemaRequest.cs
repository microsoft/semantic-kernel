// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCreateCollectionSchemaRequest
{
    private const string ApiRoute = "schema";

    [JsonConstructor]
    public WeaviateCreateCollectionSchemaRequest() { }

    public WeaviateCreateCollectionSchemaRequest(WeaviateCollectionSchema collectionSchema)
    {
        this.CollectionName = collectionSchema.CollectionName;
        this.VectorConfigurations = collectionSchema.VectorConfigurations;
        this.Properties = collectionSchema.Properties;
    }

    [JsonPropertyName("class")]
    public string? CollectionName { get; set; }

    [JsonPropertyName("vectorConfig")]
    public Dictionary<string, WeaviateCollectionSchemaVectorConfig>? VectorConfigurations { get; set; }

    [JsonPropertyName("properties")]
    public List<WeaviateCollectionSchemaProperty>? Properties { get; set; }

    public HttpRequestMessage Build()
    {
        return HttpRequest.CreatePostRequest(ApiRoute, this);
    }
}
