// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateGetCollectionSchemaResponse
{
    [JsonPropertyName("class")]
    public string? CollectionName { get; set; }
}
