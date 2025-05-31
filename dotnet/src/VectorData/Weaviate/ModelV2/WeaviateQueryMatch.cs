// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateQueryMatch
{
    [JsonPropertyName("class")]
    public string? CollectionName { get; set; }

    [JsonPropertyName("where")]
    public WeaviateQueryMatchWhereClause? WhereClause { get; set; }
}
