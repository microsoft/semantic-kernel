// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateVectorSearchResponse
{
    [JsonPropertyName("data")]
    public WeaviateVectorSearchData? Data { get; set; }
}
