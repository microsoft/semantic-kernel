// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate.ModelV2;

internal sealed class WeaviateCollectionSchemaVectorConfig
{
    [JsonPropertyName("vectorIndexType")]
    public string? VectorIndexType { get; set; }
}
