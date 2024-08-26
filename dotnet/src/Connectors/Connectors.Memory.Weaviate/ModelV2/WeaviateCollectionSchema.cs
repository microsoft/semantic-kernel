// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCollectionSchema
{
    [JsonPropertyName("class")]
    public string? CollectionName { get; set; }

    [JsonPropertyName("vectorConfig")]
    public Dictionary<string, WeaviateCollectionSchemaVectorConfig> VectorConfigurations { get; set; } = [];

    [JsonPropertyName("properties")]
    public List<WeaviateCollectionSchemaProperty> Properties { get; set; } = [];
}
