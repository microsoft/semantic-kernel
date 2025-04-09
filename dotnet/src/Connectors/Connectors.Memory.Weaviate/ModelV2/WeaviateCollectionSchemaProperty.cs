// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateCollectionSchemaProperty
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("dataType")]
    public List<string> DataType { get; set; } = [];

    [JsonPropertyName("indexFilterable")]
    public bool IndexFilterable { get; set; }

    [JsonPropertyName("indexSearchable")]
    public bool IndexSearchable { get; set; }
}
