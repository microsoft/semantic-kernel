// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCollectionSchemaVectorIndexConfig
{
    [JsonPropertyName("distance")]
    public string? Distance { get; set; }
}
