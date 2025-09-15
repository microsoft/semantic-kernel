// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCollectionSchemaVectorConfig
{
    [JsonPropertyName("vectorizer")]
    public Dictionary<string, object?> Vectorizer { get; set; } = new() { [WeaviateConstants.DefaultVectorizer] = null };

    [JsonPropertyName("vectorIndexType")]
    public string? VectorIndexType { get; set; }

    [JsonPropertyName("vectorIndexConfig")]
    public WeaviateCollectionSchemaVectorIndexConfig? VectorIndexConfig { get; set; }
}
