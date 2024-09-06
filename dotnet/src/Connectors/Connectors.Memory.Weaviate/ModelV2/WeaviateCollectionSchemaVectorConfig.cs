// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCollectionSchemaVectorConfig
{
    private const string DefaultVectorizer = "none";

    [JsonPropertyName("vectorizer")]
    public Dictionary<string, object?> Vectorizer { get; set; } = new() { [DefaultVectorizer] = null };

    [JsonPropertyName("vectorIndexType")]
    public string? VectorIndexType { get; set; }

    [JsonPropertyName("vectorIndexConfig")]
    public WeaviateCollectionSchemaVectorIndexConfig? VectorIndexConfig { get; set; }
}
