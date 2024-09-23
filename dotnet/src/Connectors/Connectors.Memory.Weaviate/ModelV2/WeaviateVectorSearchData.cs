// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Vector search data model.
/// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql"/>.
/// </summary>
internal sealed class WeaviateVectorSearchData
{
    [JsonPropertyName("Get")]
    public Dictionary<string, JsonArray>? GetOperation { get; set; }
}
